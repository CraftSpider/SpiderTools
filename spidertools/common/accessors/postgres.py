
import logging

from . import base


log = logging.getLogger("spidertools.common.accessors")
_Sentinel = object()


class PostgresAccessor(base.DatabaseAccessor):
    """
        Database accessor for connection to a Postgres database
    """

    __slots__ = ("_schema",)

    def create_connection(self, *, user, password, host, port, schema, autocommit):
        """
            Create a new database connection
        :param user: Database username
        :param password: Database password
        :param host: Host location of the database
        :param port: Port of the database
        :param schema: Schema name to use
        :param autocommit: Whether to autocommit changes
        """
        self._schema = schema
        import psycopg2
        try:
            cnx = psycopg2.connect(user=user, password=password, host=host, port=port, dbname=schema)
        except psycopg2.OperationalError:
            import psycopg2.extensions
            log.info("Requested database non-extant, creating")
            cnx = psycopg2.connect(user=user, password=password, host=host, port=port)
            cnx.autocommit = True
            cnx.cursor().execute(f"CREATE DATABASE {schema}")
            cnx.cursor().execute(f"CREATE SCHEMA {schema}")
            cnx.close()
            cnx = psycopg2.connect(user=user, password=password, host=host, port=port, dbname=schema)
        if cnx is None:
            return False

        cnx.autocommit = True
        cnx.cursor().execute(f"SET search_path TO {schema}")
        self._connection = cnx
        self._cursor = cnx.cursor()
        return True

    def execute(self, query, params=None, multi=False):
        """
            Execute a query with the given params, optionally allowing multi-query execution
        :param query: Query to execute
        :param params: Parameters to pass to the query
        :param multi: Whether to allow multi-query
        """
        return self._cursor.execute(query, params)

    def get_schemata(self):
        """
            Get a list of information about the databases's available schemata
        :return: List of schemata info tuples
        """
        self.execute(
            "SELECT * FROM information_schema.SCHEMATA"
        )
        return self._cursor.fetchall()

    def current_schema(self):
        """
            Get the current schema in use by the database
        :return: Current in-use schema
        """
        self.execute("SELECT CURRENT_SCHEMA()")
        result = self._cursor.fetchone()
        if result is None:
            return self._schema
        return result[0]

    def create_schema(self, schema):
        """
            Create a new schema in the database
        :param schema: Name of the new schema
        """
        self.execute(f"CREATE SCHEMA {schema}")

    def has_schema(self, schema):
        """
            Check whether the database contains a desired schema
        :param schema: Schema name to check
        :return: Whether schema exists in database
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s LIMIT 1",
            [schema]
        )
        return self._cursor.fetchone()[0] == 1

    def create_table(self, name, columns, primary_keys=None, foreign_keys=None):
        """
            Create a new table in the current schema.
        :param name: Name of the new table
        :param columns: Columns to create, takes the form of a dict with "name" and "type" params, minimally
        :param primary_keys: List of primary key names
        :param foreign_keys: List of foreign keys, of the form of a dict with "local_name" and "remote_table" params,
                             minimally
        """
        query = f"CREATE TABLE {self.current_schema()}.{name} ("

        lines = []

        for i in columns:
            name = i["name"]
            sql_type = i["type"]
            not_null = i.get("not_null", False)
            unique = i.get("is_unique", False)
            default = i.get("default", _Sentinel)

            column = f"{name} {sql_type}"
            if not_null:
                column += " NOT NULL"
            if unique:
                column += " UNIQUE"
            if default is not _Sentinel:
                if default is None:
                    default = "null"
                elif isinstance(default, str):
                    default = f"\'{default}\'"

                column += f" DEFAULT {default}"

            lines.append(column)

        if primary_keys is not None:
            lines.append("PRIMARY KEY (" + ", ".join(primary_keys) + ")")

        if foreign_keys is not None:
            for i in foreign_keys:
                local_name = i["local_name"]
                remote_name = i.get("remote_name", local_name)
                remote_table = i["remote_table"]
                on_delete = i.get("on_delete", None)
                on_update = i.get("on_update", None)

                foreign = f"FOREIGN KEY ({local_name}) REFERENCES {remote_table}({remote_name})"
                if on_delete is not None:
                    foreign += f" ON DELETE {on_delete}"
                if on_update is not None:
                    foreign += f" ON UPDATE {on_update}"

                lines.append(foreign)

        query += ", ".join(lines)
        query += ")"

        self.execute(query)

    def get_tables(self):
        """
            Get a list of information about the current schema's tables
        :return: List of table info tuples
        """
        query = "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s"
        self.execute(query, [self.current_schema()])
        return self._cursor.fetchall()

    def has_table(self, name):
        """
            Check whether a given table exists in the current schema
        :param name: Name of the table
        :return: Whether the table exists
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s LIMIT 1",
            [self.current_schema(), name]
        )
        return self._cursor.fetchone()[0] == 1

    def drop_table(self, name):
        """
            Drop a given table from the current schema
        :param name: Name of the table to drop
        """
        self.execute(f"DROP TABLE {name}")

    def add_column(self, table, column, *, after=None):
        """
            Add a column to a table, optionally specifying its position
        :param table: Table to add the column to
        :param column: Column to add, same format as create_table
        :param after: Column to add it after, if supported
        """
        name = column["name"]
        type = column["type"]

        query = f"ALTER TABLE {table} ADD COLUMN {name} {type}"
        if column.get("not_null", False) is True:
            query += " NOT NULL"
        if column.get("is_unique", False) is True:
            query += " UNIQUE"

        self.execute(query)

    def get_columns(self, table):
        """
            Get a list of information about columns on a given table
        :param table: Table to get column info for
        :return: List of column info tuples
        """
        query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
        self.execute(query, [self.current_schema(), table])
        return self._cursor.fetchall()

    def has_column(self, table, column):
        """
            Check whether a column with a given name exists on a table
        :param table: Table to check
        :param column: Column to check for
        :return: Whether a column with that name exists
        """
        self.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "AND COLUMN_NAME = %s",
            [self.current_schema(), table, column]
        )
        return self._cursor.fetchone()[0] > 0

    def alter_column(self, table, column):
        """
            Change the type or constraints of a column on a table
        :param table: Table to alter
        :param column: Column to alter, same format as create_table
        """
        name = column["name"]
        type = column["type"]
        query = f"ALTER TABLE {table} ALTER COLUMN {name} {type}"
        if column.get("not_null", False) is True:
            query += " NOT NULL"
        if column.get("is_unique", False) is True:
            query += " UNIQUE"
        self.execute(query)

    def drop_column(self, table, column):
        """
            Remove a column from a table
        :param table: Table to drop column from
        :param column: Name of column to drop
        """
        self.execute(f"ALTER TABLE {self.current_schema()}.{table} DROP COLUMN {column}")

    def insert(self, table, *, values, names=None, update=False):
        """
            Insert a row into a table
        :param table: Table to insert into
        :param values: Values to insert
        :param names: Names of rows to insert
        :param update: Whether to upsert
        """
        if names and len(names) != len(values):
            raise ValueError("Number of names must match values for update")

        query = f"INSERT INTO {self.current_schema()}.{table}"\

        if names is not None:
            query += " (" + ", ".join(names) + ")"

        query += " VALUES (" + \
                 ", ".join("%s" for _ in range(len(values))) + \
                 ")"

        if update:
            if names is None:
                raise ValueError("Must supply names with update")

            # TODO: Make this an accessor method?
            self.execute("SELECT col.column_name from information_schema.TABLE_CONSTRAINTS tab, " +
                         "information_schema.CONSTRAINT_COLUMN_USAGE col WHERE " +
                         f"col.table_schema = %s AND " +
                         f"col.table_schema = tab.table_schema AND "
                         "col.constraint_name = tab.constraint_name AND " +
                         "col.table_name = tab.table_name AND " +
                         "tab.constraint_type = 'PRIMARY KEY' AND " +
                         f"col.table_name = %s", [self.current_schema(), table])
            cols = self._cursor.fetchall()
            cols = tuple(map(lambda x: x[0], cols))
            cols = ", ".join(cols)

            query += f" ON CONFLICT ({cols}) DO UPDATE SET " + ", ".join(f"{i} = EXCLUDED.{i}" for i in names)

        return self.execute(query, values)

    def count(self, table, *, where, params=None, limit=None):
        """
            Count the number of rows matching a query
        :param table: Table to count from
        :param where: Query string
        :param params: Parameters to the query
        :param limit: Max limit to count
        :return: Number of rows matching query
        """
        query = f"SELECT COUNT(*) FROM {self.current_schema()}.{table}"
        if where:
            query += f" WHERE {where}"
        if limit:
            query += f" LIMIT {limit}"
        self.execute(query, params)
        return self._cursor.fetchone()[0]

    def select(self, table, *, where, params=None, order=None, limit=None):
        """
            Select rows from a table matching a query
        :param table: Table to select from
        :param where: Query string
        :param params: Parameters to the query
        :param order: How to order the result
        :param limit: Max limit of rows to select
        :return: List of tuples of row data
        """
        query = f"SELECT * FROM {self.current_schema()}.{table}"
        if where:
            query += f" WHERE {where}"
        if order:
            query += f" ORDER BY {order}"
        if limit:
            query += f" LIMIT {limit}"
        self.execute(query, params)
        return self._cursor.fetchall()

    def delete(self, table, *, where, params=None, order=None, limit=None):
        """
            Delete rows from a table matching a query
        :param table: Table to delete from
        :param where: Query string
        :param params: Parameters to the query
        :param order: How to order the deletion
        :param limit: Max limit of rows to delete
        """
        query = f"DELETE FROM {self.current_schema()}.{table}"
        if where:
            query += f" WHERE {where}"
        if order:
            query += f" ORDER BY {order}"
        if limit:
            query += f" LIMIT {limit}"
        self.execute(query, params)

    def create_trigger(self, name, cause, table, for_each, text):
        """
            Create a new trigger on the database
        :param name: Name of the trigger
        :param cause: Cause of the trigger
        :param table: Table the trigger is on
        :param for_each: Row or statement
        :param text: Functional code of the trigger
        """
        schema = self.current_schema()
        # Postgres doesn't support the full trigger spec, so we need to fake it
        query1 = f"CREATE OR REPLACE FUNCTION {schema}.st_trigger_{name}() RETURNS trigger AS $BODY$ BEGIN " \
                 f"{text} " \
                 f"END; $BODY$ LANGUAGE plpgsql"
        print(query1)
        self.execute(query1)
        query = f"CREATE TRIGGER {schema}.{name} {cause} ON {schema}.{table} FOR EACH {for_each} BEGIN EXECUTE FUNCTION st_trigger_{name} END;"
        self.execute(query)

    def get_triggers(self):
        """
            Get a list of triggers on the current database schema
        :return: List of tuples of trigger info
        """
        self.execute("SELECT * FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = %s", [self.current_schema()])
        return self._cursor.fetchall()

    def drop_trigger(self, trigger):
        """
            Drop a trigger from the current schema by name
        :param trigger: Name of trigger to drop
        """
        self.execute(f"DROP FUNCTION st_trigger_{trigger}")
        self.execute(f"DROP TRIGGER {trigger}")
