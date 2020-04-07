
import logging

from . import accessors, data, clstools


log = logging.getLogger("spidertools.common.sql")

_caches = {}


def and_from_dict(kwargs):
    """
        Generate a SQL And statement from a dict of keyword args
    :param kwargs: Keyword arguments dict
    :return: String AND statement
    """
    return " AND ".join(f"{x} = %({x})s" if kwargs[x] is not None else f"{x} is %({x})s" for x in kwargs)


def key_from_dict(kwargs):
    """
        Generator a key for a dictionary from a set of keyword arguments and their values. Used for the cache SQL
        lookups. frozenset, so that lookup order doesn't matter
    :param kwargs: Arguments to generate key from
    :return: frozenset of string keys generated from arguments
    """
    return frozenset(f"{x}|{kwargs[x]}" for x in kwargs)


def cached(func):
    """
        Marks a method as cached, meaning that it will not actually poll the database,
        if there hasn't been a database write since the last call.
    :param func: Function to convert to a cached function
    :return: New function, stores result in cache and doesn't call again till cache is invalidated
    """

    _caches[func] = {}
    _cache = _caches[func]

    def cache_check(self, type, *args, **kwargs):
        expr = key_from_dict(kwargs)
        if _cache.get(type, None) is not None and _cache[type].get(expr, None) is not None:
            return _cache[type][expr]
        result = func(self, type, *args, **kwargs)
        _cache.setdefault(type, {})[expr] = result
        return result

    cache_check.__doc__ = func.__doc__
    cache_check.__wrapped__ = func
    
    return cache_check


def invalidate(func):
    """
        Marks a function as invalidating the cache for a given type
    :param func: Function to apply cache invalidation
    :return: New function, invalidates cache when called
    """

    def cache_invalidate(self, *args, **kwargs):
        if len(args) > 0:
            t = args[0]
            if not isinstance(t, type):
                t = type(t)
            for key in _caches:
                try:
                    del _caches[key][t]
                except KeyError:
                    pass
        else:
            for key in _caches:
                _caches[key].clear()
        return func(self, *args, **kwargs)

    cache_invalidate.__doc__ = func.__doc__
    cache_invalidate.__wrapped__ = func

    return cache_invalidate


class GenericDatabase:
    """
        Class for handling a connection to a database that fits the a schema, as defined by a custom JSON format.
        (Database schema can be updated to match file with verify_schema)
    """

    __slots__ = ("_accessor", "_username", "_password", "_schema", "_host", "_port", "_schemadef")

    def __init__(self, address, port, username, password, schema, schemadef, *, connect=True):
        """
            Initializes a GenericDatabase object. If passed None, then it replaces the cursor with a dummy class.
        :param address: Address of the SQL database
        :param port: Port of the SQL database
        :param username: SQL username
        :param password: SQL password
        :param schema: SQL schema
        :param schemadef: SQL Schema definition dict
        """
        self._username = username
        self._password = password
        self._schema = schema
        self._host = address
        self._port = port
        self._schemadef = schemadef

        flavor = schemadef["sql_flavor"].lower()
        if flavor == "mysql":
            self._accessor = accessors.MysqlAccessor()
        elif flavor == "postgresql" or flavor == "postgres":
            self._accessor = accessors.PostgresAccessor()
        else:
            raise ValueError(f"Unrecognized SQL flavor {flavor}")

        if connect:
            self.reset_connection()

    def verify_schema(self):
        """
            Verifies the schema of the connected Database. If the expected schema doesn't exist, or it doesn't match the
            expected table forms, it will be updated to match. This requires basically root on the database.
        """
        out = {"tables": 0, "columns_add": 0, "columns_remove": 0}
        tables = self._schemadef.get("tables", {})
        triggers = self._schemadef.get("triggers", {})

        if not self.is_connected():
            log.warning("Attempt to verify schema when database not connected")
            return

        # Verify schema is extant
        if self._accessor.has_schema(self._schema):
            log.info(f"Found schema {self._schema}")
        else:
            log.warning(f"Schema {self._schema} doesn't exist, creating schema")
            self._accessor.create_schema(self._schema)

        # Verify tables match expected
        for table in tables:
            if self.has_table(table):
                log.info(f"Found table {table}")

                from collections import defaultdict
                columndat = defaultdict(lambda: [0, ""])
                columns = self.get_columns(table)
                for item in columns:
                    columndat[item.name][0] += 1
                    columndat[item.name][1] = item.type
                for item in tables[table]["columns"]:
                    name, col_type = item["name"], item["type"]
                    if col_type == "serial":
                        col_type = "integer"
                    elif self._schemadef["sql_flavor"] != "mysql" and col_type.startswith("varchar"):
                        col_type = "character varying"
                    columndat[name][0] += 2
                    columndat[name][1] = columndat[name][1] == col_type

                for name in columndat:
                    exists, type_match = columndat[name]
                    if exists == 1:
                        log.warning(f"  Found column {name} that shouldn't exist, removing")
                        out["columns_remove"] += 1
                        self._accessor.drop_column(table, name)
                    elif exists == 2:
                        log.warning(f"  Could not find column {name}, creating column")
                        out["columns_add"] += 1
                        column_spec = next(filter(lambda x: x["name"] == name, tables[table]["columns"]))
                        column_index = tables[table]["columns"].index(column_spec)
                        if column_index == 0:
                            after = None
                        else:
                            after = tables[table]["columns"][column_index-1]["name"]
                        self._accessor.add_column(table, column_spec, after=after)
                    elif exists == 3 and type_match is not True:
                        log.warning(f"  Column {name} didn't match expected type, attempting to fix.")
                        column_spec = next(filter(lambda x: x["name"] == name, tables[table]["columns"]))
                        self._accessor.alter_column(table, column_spec)
                    else:
                        log.info(f"  Found column {name}")
            else:
                log.info(f"Could not find table {table}, creating table")
                out["tables"] += 1
                self._accessor.create_table(
                    table,
                    tables[table]["columns"],
                    tables[table].get("primary"),
                    tables[table].get("foreign")
                )

        # Fill tables with default values
        for table in tables:
            if tables[table].get("defaults") is not None:
                names = list(map(lambda x: x["name"], tables[table]["columns"]))
                for values in tables[table]["defaults"]:
                    self._accessor.insert(table, names=names, values=values, update=True)

        # Drop existing triggers
        old_triggers = self.get_triggers()
        for trigger in old_triggers:
            self._accessor.drop_trigger(trigger.name)

        # Add all triggers
        for name in triggers:
            cause = triggers[name]["cause"]
            table = triggers[name]["table"]
            for_each = triggers[name]["for_each"]
            text = triggers[name]["text"]
            self._accessor.create_trigger(name, cause, table, for_each, text)

        return out

    def commit(self):
        """
            Commits any changes to the SQL database.
        :return: Whether a commit successfully occurred
        """
        log.debug("Committing data")
        if self._accessor.is_connected():
            self._accessor._connection.commit()
            return True
        return False

    def is_connected(self):
        """
            Checks whether we are currently connected to a database
        :return: Whether the connection exists and the cursor isn't an EmptyCursor.
        """
        return self._accessor.is_connected()

    def reset_connection(self):
        """
            Reset the database connection, commit if one currently exists and make a new database connection.
            If connection fails, it is set to None and cursor is the empty cursor
        """

        if self._accessor.is_connected():
            self._accessor.close()

        try:
            cnx = self._accessor.create_connection(
                user=self._username,
                password=self._password,
                host=self._host,
                port=self._port,
                schema=self._schema,
                autocommit=True
            )
            if cnx is False:
                log.warning("Database missing, no data will be saved this session.")
        except Exception as e:
            log.warning(e)
            log.warning("Database connection dropped, no data will be saved this session.")

    def raw_exec(self, statement, *args):
        """
            Executes a SQL statement raw and returns the result. Should only be used in dev operations.
        :param statement: SQL statement to execute.
        :return: The result of a cursor fetchall after the statement executes.
        """
        self._accessor.execute(statement, args)
        return self._accessor._cursor.fetchall()

    def execute(self, statement, args=None):
        """
            Executes a SQL statement with checks for certain connection errors that will trigger an automatic
            reconnection and retry.
        :param statement: Statement to execute
        :param args: Arguments to supply to the statement
        """
        result = self._accessor.execute(statement, args)
        if result is accessors.ConnectionLost:
            self.reset_connection()
            result = self._accessor.execute(statement, args)
        return result

    # Meta methods

    def get_schemata(self):
        """
            Get a list of Schema objects from the information_schema
        :return: list of Schema objects
        """
        return [data.Schema(x) for x in self._accessor.get_schemata()]

    def has_schema(self, schema):
        """
            Check whether the database contains a given schema
        :param schema: Schema to check existence of
        :return: Whether schema exists
        """
        return self._accessor.has_schema(schema)
    
    def get_tables(self):
        """
            Get a list of Table objects from the information_schema for the current database schema
        :return: list of Table objects
        """
        return [data.Table(x) for x in self._accessor.get_tables()]

    def has_table(self, table):
        """
            Check if the current schema has a table matching the given table name
        :param table: Name to check
        :return: Whether table exists in schema
        """
        return self._accessor.has_table(table)

    def get_columns(self, table):
        """
            Gets the column names and types of a specified table
        :param table: Name of the table to retrieve columnns from
        :return: List of column names and data types, or None if table doesn't exist
        """
        return [data.Column(x) for x in self._accessor.get_columns(table)]

    def has_column(self, table, column):
        """
            Check if a given table has a column matching the given column name. Assumes that table exists
        :param table: Table to check
        :param column: Column name to check
        :return: Whether column exists in table
        """
        return self._accessor.has_column(table, column)

    def get_triggers(self):
        """
            Gets the trigger data for the current schema
        :return: List of Trigger objects
        """
        return [data.Trigger(x) for x in self._accessor.get_triggers()]

    # Generic methods

    @clstools.invalidating_cache(method=True)
    def get_item(self, type, *, order=None, default=None, **kwargs):
        """
            Get the first GenericDatabase compatible object from the database, based on a type.
            Result can be ordered and filtered.
        :param type: GenericDatabase compatible type. Subclasses Row or duck types it
        :param order: Parameter to pass into the ORDER BY clause
        :param default: What to return if nothing is found. Defaults to None
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: An instance of type, or default
        """
        conditions = and_from_dict(kwargs)
        result = self._accessor.select(
            type.table_name(), where=conditions, params=kwargs, order=order, limit=1
        )
        if len(result) == 0:
            return default
        return type(result[0])

    @clstools.invalidating_cache(method=True)
    def get_items(self, type, *, limit=None, order=None, **kwargs):
        """
            Get a list of GenericDatabase compatible objects from the database, based on a type.
            Result can be ordered, limited, and filtered.
        :param type: GenericDatabase compatible type. Subclasses Row or duck types it
        :param limit: Maximum number of items to get. If this would be one, consider get_item
        :param order: Parameter to pass to the ORDER BY clause
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: A list of type, may be empty if nothing found
        """
        conditions = and_from_dict(kwargs)
        if isinstance(limit, tuple):
            limit = f"{limit[0]},{limit[1]}"
        return [type(x) for x in self._accessor.select(type.table_name(), where=conditions, params=kwargs, order=order, limit=limit)]

    @clstools.invalidating_cache(method=True)
    def get_count(self, type, **kwargs):
        """
            Get the number of given GenericDatabase objects that are in the database, matching the kwargs filter
        :param type: GenericDatabase compatible type. Subclasses Row or duck types it
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: Number of type in the database
        """
        conditions = and_from_dict(kwargs)
        return self._accessor.count(type.table_name(), where=conditions, params=kwargs)[0]

    @clstools.cache_invalidator(func=(get_item, get_items, get_count), method=True, args=0, generic=True)
    def save_item(self, item):
        """
            Save any GenericDatabase compatible object to the database, inserting or updating that row.
        :param item: Item to save. May be a Row, a MultiRow, or any duck type of those two.
        """
        try:
            table_name = item.table_name()
            if not isinstance(table_name, str):
                raise ValueError(f"Row table_name must be an instance of string, not {type(table_name).__name__}")
            row = item.to_row()
            columns = []
            for index, column in enumerate(self._schemadef["tables"][table_name]["columns"]):  # TODO: encapsulate this in accessor
                if column["type"] == "serial":
                    del row[index]
                else:
                    columns.append(column["name"])
            self._accessor.insert(table_name, values=row, names=columns, update=True)
        except AttributeError:
            for row in item:
                self.save_item(row)
            try:
                removed_items = item.removed_items()
                for removed in removed_items:
                    self.remove_item(removed)
            except AttributeError:  # So iterables not having this property are just ignored
                pass

    @clstools.cache_invalidator(func=(get_item, get_items, get_count), method=True, args=0, generic=True)
    def remove_item(self, item, general=False):
        """
            Remove any GenericDatabase compatible object from the database.
        :param item: Item to remove. May be a Row, a MultiRow, or any duck type of those two.
        :param general: Whether to delete all similar items. If true, nulls aren't included in the delete search
        """
        try:
            table_name = item.table_name()
            row = item.to_row()
            columns = list(map(
                lambda x: x["name"],
                self._schemadef["tables"][table_name]["columns"]
            ))
            if not general:
                params = {i: v for i, v in zip(columns, row)}
                delete_str = and_from_dict(params)
            else:
                params = {i: v for i, v in zip(columns, row) if v is not None}
                delete_str = and_from_dict(params)
            self._accessor.delete(table_name, where=delete_str, params=params)
        except AttributeError:
            for row in item:
                self.remove_item(row, general)

    @clstools.cache_invalidator(func=(get_item, get_items, get_count), method=True, args=0)
    def remove_items(self, type, *, limit=None, order=None, **kwargs):
        """
            Remove any GenericDatabase objects from the database of a specific type, that match the given parameters
            Objects to delete can be limited and ordered
        :param type: GenericDatabase compatible type. Subclasses Row or duck types it
        :param limit: Maximum number of items to delete. If this would be one, consider remove_item
        :param order: Parameter to pass into the ORDER BY clause
        :param kwargs: Parameters to filter by. Are all ANDed together
        """
        conditions = and_from_dict(kwargs)
        if isinstance(limit, tuple):
            limit = f"{limit[0]},{limit[1]}"
        self._accessor.delete(type.table_name(), where=conditions, order=order, limit=limit)
