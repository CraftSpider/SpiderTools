
import abc
import datetime as dt


class _EmptyVal:
    """
        An entirely missing value, not just present but null
    """

    def __eq__(self, other):
        """
            Any _EmptyVal is equal to any other
        :param other: Other value to check equality of
        :return: Whether other is also an _EmptyVal
        """
        return isinstance(other, _EmptyVal)


_Empty = _EmptyVal()


class Row(metaclass=abc.ABCMeta):
    """
        Conceptually, a Row in a SQL database. Subclass to define a table, __slots__ is used to define
        the columns in order. Can be saved and loaded from a database
    """

    __slots__ = ()

    def __init__(self, row, conv_bool=False):
        """
            Initializer for a row. Handles magical __slots__ initialization
        :param row: Sequence of items pulled from a table
        :param conv_bool: Whether to convert 0's and 1's to boolean values or not
        """
        if self.__class__ == Row:
            raise TypeError("Can't instantiate a non-subclassed row")

        for index in range(len(self.__slots__)):
            slot = self.__slots__[index]
            value = row[index]
            if conv_bool and (value == 0 or value == 1):
                value = bool(value)
            setattr(self, slot, value)

    def __str__(self):
        """
            Convert a Row to a string. Takes the form of `Name(value1, value2, ...)`
        :return: String form of Row
        """
        return f"{type(self).__name__}({', '.join(str(getattr(self, x)) for x in self.__slots__)})"

    def __repr__(self):
        """
            Convert a Row to its repr. Takes the form of `Name(repr(value1), repr(value2), ...)`
        :return: Repr form of Row
        """
        return f"{type(self).__name__}([{', '.join(repr(getattr(self, x)) for x in self.__slots__)}])"

    def __eq__(self, other):
        """
            Check equality of one Row to another
        :param other: Other object to check equality of
        :return: Whether other object has same column names and same values in them
        """
        if not isinstance(other, Row):
            return NotImplemented
        for slot in self.__slots__:
            sval = getattr(self, slot, _Empty)
            oval = getattr(other, slot, _Empty)
            if sval == _Empty or oval == _Empty:
                return False
            if sval != oval:
                return False
        return True

    def to_row(self):
        """
            Convert Row to a Sequence of correct length with correct data values
        :return: Sequence of SQL Storable values
        """
        out = []
        for slot in self.__slots__:
            value = getattr(self, slot)
            if isinstance(value, SqlConvertable):
                value = value.sql_safe()
            out.append(value)
        return out

    @classmethod
    def table_name(cls):
        """
            Get the name of the table this Row object is associated with
        :return: Name of a SQL table
        """
        if hasattr(cls, "TABLE_NAME"):
            return cls.TABLE_NAME
        else:
            return None


class MultiRow(metaclass=abc.ABCMeta):
    """
        An object containing multiple different rows, possibly from multiple tables.
        Can be saved and loaded from a Database like a Row
    """

    __slots__ = ("_removed",)

    def __init__(self, data):
        """
            Initialize this MultiRow with given data. Uses slot names to pull from dict into self attributes
        :param data: Dict of data to pull Rows or lists of Rows from
        """
        self._removed = []
        for slot in self.__slots__:
            value = data.get(slot)
            setattr(self, slot, value)

    def __iter__(self):
        """
            Return an iterable of all Row like objects or iterable of row like objects in the MultiRow.
            Override this if not all slots are Rows or iterables of rows
        :return: Iterable of rows or iterable containing rows
        """
        return self.items()

    def __eq__(self, other):
        """
            Check equality between this and another MultiRow. Works similarly to Row
        :param other: Other object to check against
        :return: Whether this object is equal to Other
        """
        if not isinstance(other, MultiRow):
            return False
        for slot in self.__slots__:
            sval = getattr(self, slot, _Empty)
            oval = getattr(self, slot, _Empty)
            if sval == _Empty or oval == _Empty:
                return False
            if sval != oval:
                return False
        return True

    def items(self):
        """
            Get an iterable of all Row like objects or iterable of row like objects in the MultiRow.
            Override this if not all slots are Rows or iterables of rows
        :return: Iterable of rows or iterable containing rows
        """
        return iter(getattr(self, x) for x in self.__slots__)

    @abc.abstractmethod
    def removed_items(self):
        """
            Return a list of any items removed from this row during its time in memory. Ensures they will be removed
            from the database when this object is saved.
        :return: List of Row objects
        """


class SqlConvertable(metaclass=abc.ABCMeta):
    """
        Class representing a type that is not a SQL safe type, but can be converted to one
        Generally used inside a Row
    """

    __slots__ = ()

    def __eq__(self, other):
        """
            Equality between SqlConvertable instances is based on whether their safe forms
            are qual to each other
        :param other: Other convertable to check with
        :return: Whether sql_safe forms are equal
        """
        if isinstance(other, SqlConvertable):
            return self.sql_safe() == other.sql_safe()
        return NotImplemented

    @abc.abstractmethod
    def sql_safe(self):
        """
            Convert this object to a form that can be stored in a SQL database. Can be any SQL safe type. This object,
            if fed into the constructor, should recreate the current SqlConvertable.
        :return: Object in a raw storable form
        """


class Schema(Row):
    """
        Information Schema SCHEMA Table
    """

    __slots__ = ("catalog", "name", "default_character_set", "default_collation", "sql_path", "default_encryption")


class Table(Row):
    """
        Information Schema TABLES Table
    """

    __slots__ = ("catalog", "schema", "name", "type", "engine", "version", "row_format", "num_rows", "avg_row_len",
                 "data_len", "max_data_len", "index_len", "data_free", "auto_increment", "create_time", "update_time",
                 "check_time", "table_collation", "checksum", "create_options", "table_commentx")


class Column(Row):
    """
        Information Schema COLUMNS Table
    """

    __slots__ = ("catalog", "schema", "table_name", "name", "position", "default", "nullable", "type", "char_max_len",
                 "bytes_max_len", "numeric_precision", "numeric_scale", "datetime_precision", "char_set_name",
                 "collation_name", "column_type", "column_key", "extra", "privileges", "comment", "generation_expr")


class Trigger(Row):
    """
        Information Schema TRIGGERS Table
    """

    __slots__ = ("catalog", "schema", "name", "event_manipulation", "event_object_catalog", "event_object_schema",
                 "event_object_table", "action_order", "action_condition", "action_statement", "action_orientation",
                 "action_timing", "action_reference_old_table", "action_reference_new_table",
                 "action_reference_old_row", "action_reference_new_row", "created", "sql_mode", "definer",
                 "character_set_client", "collation_connection", "database_collation")
