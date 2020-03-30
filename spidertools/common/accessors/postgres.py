
import logging

from . import base


log = logging.getLogger("spidertools.common.accessors")
_Sentinel = object()


class PostgresAccessor(base.DatabaseAccessor):

    def create_connection(self, *, user, password, host, port, schema, autocommit):
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
        return self._cursor.execute(query, params)

    def get_schemata(self):
        self.execute(
            "SELECT * FROM information_schema.SCHEMATA"
        )
        return self._cursor.fetchall()

    def current_schema(self):
        self.execute("SELECT CURRENT_SCHEMA()")
        result = self._cursor.fetchone()
        if result is None:
            return self._schema
        return result[0]

    def create_schema(self, schema):
        self.execute(f"CREATE SCHEMA {schema}")

    def has_schema(self, schema):
        self.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s LIMIT 1",
            [schema]
        )
        return self._cursor.fetchone()[0] == 1

    def create_table(self, name, columns, primary_keys=None, foreign_keys=None):
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
        query = "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s"
        self.execute(query, [self.current_schema()])
        return self._cursor.fetchall()

    def has_table(self, name):
        self.execute(
            "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s LIMIT 1",
            [self.current_schema(), name]
        )
        return self._cursor.fetchone()[0] == 1

    def drop_table(self, name):
        self.execute(f"DROP TABLE {name}")

    def add_column(self, table, column, *, after=None):
        name = column["name"]
        type = column["type"]

        query = f"ALTER TABLE {table} ADD COLUMN {name} {type}"
        if column.get("not_null", False) is True:
            query += " NOT NULL"
        if column.get("is_unique", False) is True:
            query += " UNIQUE"

        self.execute(query)

    def get_columns(self, table):
        query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
        self.execute(query, [self.current_schema(), table])
        return self._cursor.fetchall()

    def has_column(self, table, column):
        self.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
            "AND COLUMN_NAME = %s",
            [self.current_schema(), table, column]
        )
        return self._cursor.fetchone()[0] > 0

    def alter_column(self, table, column):
        name = column["name"]
        type = column["type"]
        query = f"ALTER TABLE {table} ALTER COLUMN {name} {type}"
        if column.get("not_null", False) is True:
            query += " NOT NULL"
        if column.get("is_unique", False) is True:
            query += " UNIQUE"
        self.execute(query)

    def drop_column(self, table, column):
        self.execute(f"ALTER TABLE {self.current_schema()}.{table} DROP COLUMN {column}")

    def insert(self, table, *, values, names=None, update=False):
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
        query = f"SELECT COUNT(*) FROM {self.current_schema()}.{table}"
        if where:
            query += f" WHERE {where}"
        if limit:
            query += f" LIMIT {limit}"
        self.execute(query, params)
        return self._cursor.fetchone()[0]

    def select(self, table, *, where, params=None, order=None, limit=None):
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
        query = f"DELETE FROM {self.current_schema()}.{table}"
        if where:
            query += f" WHERE {where}"
        if order:
            query += f" ORDER BY {order}"
        if limit:
            query += f" LIMIT {limit}"
        self.execute(query, params)

    def get_triggers(self):
        self.execute("SELECT * FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = %s", [self.current_schema()])
        return self._cursor.fetchall()

    def drop_trigger(self, trigger):
        self.execute(f"DROP TRIGGER {trigger}")

