
import logging
import re
import mysql.connector
import mysql.connector.abstracts as mysql_abstracts

from spidertools.common import data

log = logging.getLogger("talos.utils.sql")


class EmptyCursor(mysql_abstracts.MySQLCursorAbstract):
    """
        A cursor for a non-existent database that should pretend to be connected. Returns None or empty list values
        for all results
    """

    __slots__ = ()

    DEFAULT_ONE = None
    DEFAULT_ALL = list()

    def __init__(self):
        """Init stub"""
        super().__init__()

    def __iter__(self):
        """Iterator stub"""
        return iter(self.fetchone, self.DEFAULT_ONE)

    def callproc(self, procname, args=()):
        """Callproc stub"""
        pass

    def close(self):
        """Close stub"""
        pass

    def execute(self, query, params=None, multi=False):
        """Execute stub"""
        pass

    def executemany(self, operation, seqparams):
        """Executemany stub"""
        pass

    def fetchone(self):
        """Fetchone stub"""
        return self.DEFAULT_ONE

    def fetchmany(self, size=1):
        """Fetchmany stub"""
        return self.DEFAULT_ALL

    def fetchall(self):
        """Fetchall stub"""
        return self.DEFAULT_ALL

    @property
    def description(self):
        """Description stub"""
        return tuple()

    @property
    def rowcount(self):
        """Rowcount stub"""
        return 0

    @property
    def lastrowid(self):
        """Lastrowid stub"""
        return None


talos_create_table = "CREATE TABLE `{}` ({}) ENGINE=InnoDB DEFAULT CHARSET=utf8"
talos_add_column = "ALTER TABLE {} ADD COLUMN {} {}"
talos_modify_column = "ALTER TABLE {} MODIFY COLUMN {}"
talos_create_trigger = "CREATE TRIGGER {} {} on {} {} END;"


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


_caches = {}


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
        Class for handling a Talos connection to a MySQL database that fits the schema expected by Talos.
        (Schema matching can be enforced with verify_schema)
    """

    __slots__ = ("_sql_conn", "_cursor", "_username", "_password", "_schema", "_host", "_port", "_schemadef")

    def __init__(self, address, port, username, password, schema, schemadef, *, connect=True):
        """
            Initializes a TalosDatabase object. If passed None, then it replaces the cursor with a dummy class.
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
        self._sql_conn = None
        self._cursor = EmptyCursor()
        self._schemadef = schemadef
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
        if self.has_schema(self._schema):
            log.info(f"Found schema {self._schema}")
        else:
            log.warning(f"Schema {self._schema} doesn't exist, creating schema")
            self.create_schema(self._schema)

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
                    details = re.search(r"`(.*?)` (\w+)", item)
                    name, col_type = details.group(1), details.group(2)
                    columndat[name][0] += 2
                    columndat[name][1] = columndat[name][1] == col_type

                for name in columndat:
                    exists, type_match = columndat[name]
                    if exists == 1:
                        log.warning(f"  Found column {name} that shouldn't exist, removing")
                        out["columns_remove"] += 1
                        self.remove_column(table, name)
                    elif exists == 2:
                        log.warning(f"  Could not find column {name}, creating column")
                        out["columns_add"] += 1
                        column_spec = next(filter(lambda x: x.find("`{}`".format(name)) > -1,
                                                  tables[table]["columns"]))
                        column_index = tables[table]["columns"].index(column_spec)
                        if column_index == 0:
                            column_place = "FIRST"
                        else:
                            column_place = "AFTER " +\
                                           re.search(
                                               r"`(.*?)`",
                                               tables[table]["columns"][column_index-1]
                                           ).group(1)
                        self.execute(talos_add_column.format(table, column_spec, column_place))
                    elif exists == 3 and type_match is not True:
                        log.warning(f"  Column {name} didn't match expected type, attempting to fix.")
                        column_spec = next(filter(lambda x: x.find("`{}`".format(name)) > -1,
                                                  tables[table]["columns"]))
                        self.execute(talos_modify_column.format(table, column_spec))
                    else:
                        log.info(f"  Found column {name}")
            else:
                log.info(f"Could not find table {table}, creating table")
                out["tables"] += 1
                body = ',\n'.join(tables[table]["columns"] + ["PRIMARY KEY " + tables[table]["primary"]])
                if "foreign" in tables[table]:
                    for key in tables[table]["foreign"]:
                        body += ",\n FOREIGN KEY " + key
                    if "cascade" in tables[table] and tables[table]["cascade"] is True:
                        body += " ON DELETE CASCADE"
                self.execute(
                    talos_create_table.format(
                        table, ',\n'.join(tables[table]["columns"] + ["PRIMARY KEY " + tables[table]["primary"]])
                    )
                )

        # Fill tables with default values
        for table in tables:
            if tables[table].get("defaults") is not None:
                for values in tables[table]["defaults"]:
                    vals = str(values).strip("[]")
                    self.execute(f"REPLACE INTO {table} VALUES ({vals})")

        # Drop existing triggers
        query = "SELECT trigger_name FROM information_schema.TRIGGERS WHERE trigger_schema = SCHEMA();"
        self.execute(query)
        old_triggers = map(lambda x: x[0], self._cursor.fetchall())
        for trigger in old_triggers:
            self.execute(f"DROP TRIGGER {trigger}")

        # Add all triggers
        for name in triggers:
            cause = triggers[name]["cause"]
            table = triggers[name]["table"]
            text = triggers[name]["text"]
            self.execute(talos_create_trigger.format(name, cause, table, text))

        return out

    def commit(self):
        """
            Commits any changes to the SQL database.
        :return: Whether a commit successfully occurred
        """
        log.debug("Committing data")
        if self._sql_conn:
            self._sql_conn.commit()
            return True
        return False

    def is_connected(self):
        """
            Checks whether we are currently connected to a database
        :return: Whether the connection exists and the cursor isn't an EmptyCursor.
        """
        return self._sql_conn is not None and not isinstance(self._cursor, EmptyCursor)

    def reset_connection(self):
        """
            Reset the database connection, commit if one currently exists and make a new database connection.
            If connection fails, it is set to None and cursor is the empty cursor
        """

        if self._sql_conn:
            try:
                self.commit()
                self._sql_conn.close()
            except Exception:
                pass

        cnx = None
        try:
            cnx = mysql.connector.connect(user=self._username, password=self._password, host=self._host,
                                          port=self._port, autocommit=True)
            if cnx is None:
                log.warning("Talos database missing, no data will be saved this session.")
            else:
                try:
                    cnx.cursor().execute(f"USE {self._schema}")
                    log.info("Talos database connection established")
                except mysql.connector.DatabaseError:
                    log.info("Talos Schema non-extant, creating")
                    try:
                        cnx.cursor().execute(f"CREATE SCHEMA {self._schema}")
                        cnx.cursor().execute(f"USE {self._schema}")
                        log.info("Talos database connection established")
                    except mysql.connector.DatabaseError:
                        log.warning("Talos Schema could not be created, dropping connection")
                        cnx = None
        except Exception as e:
            log.warning(e)
            log.warning("Database connection dropped, no data will be saved this session.")

        if cnx is not None:
            self._sql_conn = cnx
            self._cursor = cnx.cursor()
        else:
            self._sql_conn = None
            self._cursor = EmptyCursor()

    def raw_exec(self, statement, *args):
        """
            Executes a SQL statement raw and returns the result. Should only be used in dev operations.
        :param statement: SQL statement to execute.
        :return: The result of a cursor fetchall after the statement executes.
        """
        self._cursor.execute(statement, args)
        return self._cursor.fetchall()

    def execute(self, statement, args=None):
        """
            Executes a SQL statement with checks for certain connection errors that will trigger an automatic
            reconnection and retry.
        :param statement: Statement to execute
        :param args: Arguments to supply to the statement
        """
        try:
            return self._cursor.execute(statement, args)
        except mysql.connector.errors.Error as e:
            if e.errno == 2006:
                self.reset_connection()
                return self.execute(statement, args)
            else:
                raise

    # Meta methods

    def create_schema(self, schema, charset="utf8"):
        """
            Add a new schema to the database, with the given name and default charset
        :param schema: Name of the schema to create
        :param charset: Default character set of the schema
        """
        self.execute(
            f"CREATE SCHEMA {schema} DEFAULT CHARACTER SET {charset}"
        )

    def create_table(self, table, columns, primary="", foreign="", engine="InnoDB", charset="utf8"):
        """
            Add a new table to the primary schema, with a given name and set of columns
        :param table: Name of the table to create
        :param columns: List of column definitions
        :param primary: Primary keys of the table
        :param foreign: Foreign keys of the table
        :param engine: Table engine to use
        :param charset: Table charset to use
        """
        internal = ",\n".join(columns)
        if primary:
            internal += f",\nPRIMARY KEY ({primary})"
        if foreign:
            internal += f",\nFOREIGN KEY {foreign}"
        self.execute(
            f"CREATE TABLE {table} ({internal}) ENGINE={engine} DEFAULT CHARSET={charset}"
        )

    def drop_table(self, table):
        """
            Drop a table from the primary schema
        :param table: Name of the table to drop
        """
        self.execute(
            f"DROP TABLE {self._schema}.{table}"
        )

    def add_column(self, table, column, type, num="", constraint="", after=None):
        """
            Add a column to a given table in the primary schema
        :param table: Name of the table to add column to
        :param column: Name of the column to add
        :param type: Type of the column
        :param num: Number for the column type
        :param constraint: Column constraints
        :param after: Where to place the column in the table
        """
        if num:
            num = f"({num})"

        if after is None:
            after = "FIRST"
        else:
            after = f"AFTER {after}"

        self.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {type}{num} {constraint} {after}"
        )

    def modify_column(self, table, column, type, num=""):
        """
            Alter a column from the given table
        :param table: Name of the table
        :param column: Name of the column
        :param type: Type to set the column type to
        :param num: Number for the column type
        """
        if num:
            num = f"({num})"
        self.execute(
            f"ALTER TABLE {table} MODIFY COLUMN {column} {type}{num}"
        )

    def remove_column(self, table, column):
        """
            Remove a column from the given table
        :param table: Table to remove column from
        :param column: Column to remove
        """
        self.execute(
            f"ALTER TABLE {self._schema}.{table} DROP COLUMN {column}"
        )

    def has_schema(self, schema):
        """
            Check whether the database contains a given schema
        :param schema: Schema to check existence of
        :return: Whether schema exists
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s LIMIT 1",
            [schema]
        )
        return self._cursor.fetchone()[0] > 0
    
    def get_tables(self):
        """
            Get a list of Table objects from the information_schema for the current database schema
        :return: list of Table objects
        """
        query = "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s"
        self.execute(query, [self._schema])
        return [data.Table(x) for x in self._cursor]

    def has_table(self, table):
        """
            Check if the current schema has a table matching the given table name
        :param table: Name to check
        :return: Whether table exists in schema
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s LIMIT 1",
            [self._schema, table]
        )
        return self._cursor.fetchone()[0] > 0

    def get_columns(self, table):
        """
            Gets the column names and types of a specified table
        :param table: Name of the table to retrieve columnns from
        :return: List of column names and data types, or None if table doesn't exist
        """
        query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
        self.execute(query, [self._schema, table])
        return [data.Column(x) for x in self._cursor]

    def has_column(self, table, column):
        """
            Check if a given table has a column matching the given column name. Assumes that table exists
        :param table: Table to check
        :param column: Column name to check
        :return: Whether column exists in table
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "AND COLUMN_NAME = %s",
            [self._schema, table, column]
        )
        return self._cursor.fetchone()[0] > 0

    # Generic methods

    @cached
    def get_item(self, type, *, order=None, default=None, **kwargs):
        """
            Get the first TalosDatabase compatible object from the database, based on a type.
            Result can be ordered and filtered.
        :param type: TalosDatabase compatible type. Subclasses Row or duck types it
        :param order: Parameter to pass into the ORDER BY clause
        :param default: What to return if nothing is found. Defaults to None
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: An instance of type, or default
        """
        conditions = and_from_dict(kwargs)
        query = f"SELECT * FROM {self._schema}.{type.table_name()}"
        if conditions:
            query += " WHERE " + conditions
        if order:
            query += f" ORDER BY {order}"
        query += " LIMIT 1"
        self.execute(query, kwargs)
        result = self._cursor.fetchone()
        if result is None:
            return default
        return type(result)

    @cached
    def get_items(self, type, *, limit=None, order=None, **kwargs):
        """
            Get a list of TalosDatabase compatible objects from the database, based on a type.
            Result can be ordered, limited, and filtered.
        :param type: TalosDatabase compatible type. Subclasses Row or duck types it
        :param limit: Maximum number of items to get. If this would be one, consider get_item
        :param order: Parameter to pass to the ORDER BY clause
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: A list of type, may be empty if nothing found
        """
        conditions = and_from_dict(kwargs)
        query = f"SELECT * FROM {self._schema}.{type.table_name()}"
        if conditions:
            query += " WHERE " + conditions
        if order is not None:
            query += f" ORDER BY {order}"
        if limit is not None:
            if isinstance(limit, tuple):
                limit = f"{limit[0]},{limit[1]}"
            query += f" LIMIT {limit}"
        self.execute(query, kwargs)
        return [type(x) for x in self._cursor]

    @cached
    def get_count(self, type, **kwargs):
        """
            Get the number of given TalosDatabase objects that are in the database, matching the kwargs filter
        :param type: TalosDatabase compatible type. Subclasses Row or duck types it
        :param kwargs: Parameters to filter by. Are all ANDed together
        :return: Number of type in the database
        """
        conditions = and_from_dict(kwargs)
        query = f"SELECT COUNT(*) FROM {self._schema}.{type.table_name()}"
        if conditions:
            query += " WHERE " + conditions
        self.execute(query, kwargs)
        return self._cursor.fetchone()[0]

    @invalidate
    def save_item(self, item):
        """
            Save any TalosDatabase compatible object to the database, inserting or updating that row.
        :param item: Item to save. May be a Row, a MultiRow, or any duck type of those two.
        """
        try:
            table_name = item.table_name()
            if not isinstance(table_name, str):
                raise ValueError(f"Row table_name must be an instance of string, not {type(table_name).__name__}")
            row = item.to_row()
            columns = list(map(
                lambda x: re.match(r"`(.*?)`", x).group(1),
                self._schemadef["tables"][table_name]["columns"]
            ))
            replace_str = ", ".join("%s" for _ in range(len(columns)))
            update_str = ", ".join(f"{i} = VALUES({i})" for i in columns)
            query = f"INSERT INTO {self._schema}.{table_name} VALUES ({replace_str}) "\
                    "ON DUPLICATE KEY UPDATE "\
                    f"{update_str}"
            log.debug(query)
            self.execute(query, row)
        except AttributeError:
            for row in item:
                self.save_item(row)
            try:
                removed_items = item.removed_items()
                for removed in removed_items:
                    self.remove_item(removed)
            except AttributeError:  # So iterables not having this property are just ignored
                pass

    @invalidate
    def remove_item(self, item, general=False):
        """
            Remove any TalosDatabase compatible object from the database.
        :param item: Item to remove. May be a Row, a MultiRow, or any duck type of those two.
        :param general: Whether to delete all similar items. If true, nulls aren't included in the delete search
        """
        try:
            table_name = item.table_name()
            row = item.to_row()
            columns = list(map(
                lambda x: re.match(r"`(.*?)`", x).group(1),
                self._schemadef["tables"][table_name]["columns"]
            ))
            if not general:
                delete_str = " AND ".join(
                    (f"{i} = %s" if v is not None else f"{i} is %s") for i, v in zip(columns, row)
                )
            else:
                delete_str = " AND ".join(
                    f"{columns[i]} = %s" for i in range(len(columns)) if getattr(item, item.__slots__[i]) is not None
                )
                row = list(filter(None, row))
            query = f"DELETE FROM {self._schema}.{table_name} WHERE {delete_str}"
            log.debug(query)
            self.execute(query, row)
        except AttributeError:
            for row in item:
                self.remove_item(row, general)

    @invalidate
    def remove_items(self, type, *, limit=None, order=None, **kwargs):
        """
            Remove any TalosDatabase objects from the database of a specific type, that match the given parameters
            Objects to delete can be limited and ordered
        :param type: TalosDatabase compatible type. Subclasses Row or duck types it
        :param limit: Maximum number of items to delete. If this would be one, consider remove_item
        :param order: Parameter to pass into the ORDER BY clause
        :param kwargs: Parameters to filter by. Are all ANDed together
        """
        conditions = and_from_dict(kwargs)
        query = f"DELETE FROM {self._schema}.{type.table_name()}"
        if conditions:
            query += " WHERE " + conditions
        if order is not None:
            query += f" ORDER BY {order}"
        if limit is not None:
            if isinstance(limit, tuple):
                limit = f"{limit[0]},{limit[1]}"
            query += f" LIMIT {limit}"
        self.execute(query, kwargs)
