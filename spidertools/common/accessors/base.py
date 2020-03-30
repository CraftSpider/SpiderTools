
import abc


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

    def __init__(self):
        self._connection = None
        self._cursor = EmptyCursor()

    @abc.abstractmethod
    def create_connection(self, *, user, password, host, port, schema, autocommit):
        raise NotImplementedError()

    @abc.abstractmethod
    def execute(self, query, params=None, multi=False):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_schemata(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def current_schema(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def create_schema(self, schema):
        raise NotImplementedError()

    @abc.abstractmethod
    def has_schema(self, schema):
        raise NotImplementedError()

    @abc.abstractmethod
    def create_table(self, name, columns, primary_keys=None, foreign_keys=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_tables(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def has_table(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_table(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_column(self, table, column, *, after=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_columns(self, table):
        raise NotImplementedError()

    @abc.abstractmethod
    def has_column(self, table, column):
        raise NotImplementedError()

    @abc.abstractmethod
    def alter_column(self, table, column):
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_column(self, table, column):
        raise NotImplementedError()

    @abc.abstractmethod
    def insert(self, table, *, values, names=None, update=False):
        raise NotImplementedError()

    @abc.abstractmethod
    def count(self, table, *, where, params=None, limit=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def select(self, table, *, where, params=None, order=None, limit=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, table, *, where, params=None, order=None, limit=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_triggers(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def drop_trigger(self, trigger):
        raise NotImplementedError()

    def is_connected(self):
        return self._connection is not None

    def close(self):
        try:
            self._connection.close()
        except Exception as e:
            log.info(f"Error while closing SQL connection: {e}")

        self._connection = None
        self._cursor = EmptyCursor()
