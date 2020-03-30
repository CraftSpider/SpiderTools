
import abc
import logging


log = logging.getLogger("spidertools.common.accessor")
ConnectionLost = object()


class EmptyCursor:
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


class DatabaseAccessor(abc.ABC):
    """
        Abstract base for Database Accessors, classes that abstract SQL differences and allow different flavors
        to be treated in the same way
    """

    __slots__ = ("_connection", "_cursor")

    def __init__(self):
        """
            Initialize a DatabaseAccessor, sets up no connection and an empty cursor
        """
        self._connection = None
        self._cursor = EmptyCursor()

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
    def execute(self, query, params=None, multi=False):
        """
            Execute a query with the given params, optionally allowing multi-query execution
        :param query: Query to execute
        :param params: Parameters to pass to the query
        :param multi: Whether to allow multi-query
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_schemata(self):
        """
            Get a list of information about the databases's available schemata
        :return: List of schemata info tuples
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def current_schema(self):
        """
            Get the current schema in use by the database
        :return: Current in-use schema
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def create_schema(self, schema):
        """
            Create a new schema in the database
        :param schema: Name of the new schema
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def has_schema(self, schema):
        """
            Check whether the database contains a desired schema
        :param schema: Schema name to check
        :return: Whether schema exists in database
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def create_table(self, name, columns, primary_keys=None, foreign_keys=None):
        """
            Create a new table in the current schema.
        :param name: Name of the new table
        :param columns: Columns to create, takes the form of a dict with "name" and "type" params, minimally
        :param primary_keys: List of primary key names
        :param foreign_keys: List of foreign keys, of the form of a dict with "local_name" and "remote_table" params,
                             minimally
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_tables(self):
        """
            Get a list of information about the current schema's tables
        :return: List of table info tuples
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def has_table(self, name):
        """
            Check whether a given table exists in the current schema
        :param name: Name of the table
        :return: Whether the table exists
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_table(self, name):
        """
            Drop a given table from the current schema
        :param name: Name of the table to drop
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_column(self, table, column, *, after=None):
        """
            Add a column to a table, optionally specifying its position
        :param table: Table to add the column to
        :param column: Column to add, same format as create_table
        :param after: Column to add it after, if supported
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_columns(self, table):
        """
            Get a list of information about columns on a given table
        :param table: Table to get column info for
        :return: List of column info tuples
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def has_column(self, table, column):
        """
            Check whether a column with a given name exists on a table
        :param table: Table to check
        :param column: Column to check for
        :return: Whether a column with that name exists
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def alter_column(self, table, column):
        """
            Change the type or constraints of a column on a table
        :param table: Table to alter
        :param column: Column to alter, same format as create_table
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_column(self, table, column):
        """
            Remove a column from a table
        :param table: Table to drop column from
        :param column: Name of column to drop
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def insert(self, table, *, values, names=None, update=False):
        """
            Insert a row into a table
        :param table: Table to insert into
        :param values: Values to insert
        :param names: Names of rows to insert
        :param update: Whether to upsert
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def count(self, table, *, where, params=None, limit=None):
        """
            Count the number of rows matching a query
        :param table: Table to count from
        :param where: Query string
        :param params: Parameters to the query
        :param limit: Max limit to count
        :return: Number of rows matching query
        """
        raise NotImplementedError()

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, table, *, where, params=None, order=None, limit=None):
        """
            Delete rows from a table matching a query
        :param table: Table to delete from
        :param where: Query string
        :param params: Parameters to the query
        :param order: How to order the deletion
        :param limit: Max limit of rows to delete
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_triggers(self):
        """
            Get a list of triggers on the current database schema
        :return: List of tuples of trigger info
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_trigger(self, trigger):
        """
            Drop a trigger from the current schema by name
        :param trigger: Name of trigger to drop
        """
        raise NotImplementedError()

    def is_connected(self):
        """
            Check whether the database is currently connected
        :return: Whether connection is active
        """
        return self._connection is not None

    def close(self):
        """
            Close the current connection, without re-opening
        """
        try:
            self._connection.close()
        except Exception as e:
            log.info(f"Error while closing SQL connection: {e}")

        self._connection = None
        self._cursor = EmptyCursor()
