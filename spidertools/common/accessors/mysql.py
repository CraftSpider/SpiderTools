
import logging

from . import base


log = logging.getLogger("spidertools.common.accessors")
_Sentinel = object()


def _transform_type(t):
    """
        Convert a type from a schema-def to a MySQL type
    :param t: Type in schemadef
    :return: MySQL equivalent
    """
    if t.lower() == "boolean" or t.lower == "bool":
        t = "tinyint(1)"
    return t


class MysqlAccessor(base.DatabaseAccessor):
    """
        Database accessor for connection to a MySQL database
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
        import mysql.connector
        cnx = mysql.connector.connect(user=user, password=password, host=host, port=port, autocommit=autocommit)
        if cnx is not None:
            try:
                self._connection.cursor().execute(f"USE {schema}")
                log.info("Talos database connection established")
            except mysql.connector.DatabaseError:
                log.info("Talos Schema non-extant, creating")
                try:
                    self._connection.cursor().execute(f"CREATE SCHEMA {schema}")
                    self._connection.cursor().execute(f"USE {schema}")
                    log.info("Talos database connection established")
                except mysql.connector.DatabaseError:
                    log.warning("Talos Schema could not be created, dropping connection")
                    cnx = None

        if cnx is None:
            return False

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
        import mysql.connector
        try:
            return self._cursor.execute(query, params)
        except mysql.connector.errors.Error as e:
            if e.errno == 2006:
                return base.ConnectionLost
            else:
                raise

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
        self.execute("SELECT DATABASE()")
        result = self._cursor.fetchone()
        if result is None:
            return self._schema
        return result[0]

    def create_schema(self, schema):
        """
            Create a new schema in the database
        :param schema: Name of the new schema
        """
        self.execute(f"CREATE SCHEMA {schema} DEFAULT CHARACTER SET utf8")

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
        query = "CREATE TABLE " + name + " ("

        lines = []

        for i in columns:
            name = i["name"]
            sql_type = _transform_type(i["type"])
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

                query = f"FOREIGN KEY ({local_name}) REFERENCES {remote_table}({remote_name})"
                if on_delete is not None:
                    query += f" ON DELETE {on_delete}"
                if on_update is not None:
                    query += f" ON UPDATE {on_update}"

                lines.append(query)

        query += ", ".join(lines)
        query += ") ENGINE=InnoDB DEFAULT CHARSET=utf8"

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

        query = f"MODIFY TABLE {table} ADD COLUMN {name} {type}"
        if column.get("not_null", False) is True:
            query += " NOT NULL"
        if column.get("is_unique", False) is True:
            query += " UNIQUE"

        if after is None:
            query += " FIRST"
        else:
            query += f" AFTER {query}"

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
        query = f"ALTER TABLE {table} MODIFY COLUMN {name} {type}"
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
        query = f"INSERT INTO {self.current_schema()}.{table} VALUES (" + \
                ", ".join("%s" for _ in range(len(values))) + \
                ")"

        if update:
            if len(names) != len(values):
                raise ValueError("Names must match values for update")

            query += " ON DUPLICATE KEY UPDATE " + ", ".join(f"{i} = VALUES({i})" for i in names)

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
            query += " WHERE " + where
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
            query += " WHERE " + where
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
        self.execute(f"DROP TRIGGER {trigger}")
