
import pytest

import os
import spidertools.common as tutils
import spidertools.common.accessors.base as base


SCHEMA = {
    "tables": {
        "test1": {
            "columns": [
                {
                    "name": "col1",
                    "type": "integer",
                    "not_null": True
                },
                {
                    "name": "col2",
                    "type": "text"
                }
            ],
            "primary": ["col1"]
        }
    }
}


class Test1(tutils.Row):

    __slots__ = ("col1", "col2")

    @classmethod
    def table_name(cls):
        return "test1"


@pytest.fixture()
def database(request):
    schemadef = SCHEMA.copy()

    schemadef["sql_flavor"] = request.param

    if request.param == "postgres":
        database = tutils.GenericDatabase("127.0.0.1", 5432, "postgres", "", "test_schema", schemadef)
    elif request.param == "mysql":
        database = tutils.GenericDatabase("127.0.0.1", 3306, "root", "", "test_schema", schemadef)

    if not database.is_connected():
        if os.getenv("CI") == "true":
            pytest.fail()
        else:
            pytest.skip("Failed to connect to MySql database")

    database.verify_schema()

    yield database


def test_empty_cursor():
    cursor = base.EmptyCursor()

    with pytest.raises(StopIteration):
        cursor.__iter__().__next__()

    assert cursor.callproc("") is None, "callproc did something"
    assert cursor.close() is None, "close did something"
    assert cursor.execute("") is None, "execute did something"
    assert cursor.executemany("", []) is None, "executemany did something"

    assert cursor.fetchone() is None, "fetchone not None"
    assert cursor.fetchmany() == list(), "fetchmany not empty list"
    assert cursor.fetchall() == list(), "fetchall not empty list"

    assert cursor.description == tuple(), "description not empty tuple"
    assert cursor.rowcount == 0, "rowcount not 0"
    assert cursor.lastrowid is None, "lastrowid not None"


def test_empty_database():
    database = tutils.GenericDatabase("", -1, "notauser", "", "talos_data", {"sql_flavor": "mysql"}, connect=False)

    assert database.is_connected() is False, "Empty database considered connected"
    assert database.raw_exec("SELECT * FROM admins") == list(), "raw_exec didn't return empty fetchall"
    assert database.commit() is False, "Database committed despite not existing?"
    assert database.execute("SELECT * FROM admins WHERE id=%s", [12345678]) is None,\
        "Database execution returned unexpected result"


@pytest.mark.parametrize("database", ["mysql", "postgres"], indirect=True)
def test_database(database: tutils.GenericDatabase):

    item1 = Test1([4, "Hello World"])
    item2 = Test1([-4, None])

    database.save_item(item1)
    database.save_item(item2)

    assert database.get_count(Test1) == 2
    assert len(database.get_items(Test1)) == 2

    assert database.get_item(Test1, col1=4) == item1
    assert database.get_item(Test1, col1=4).col2 == "Hello World"
    assert database.get_item(Test1, col1=-4) == item2
    assert database.get_item(Test1, col1=-4).col2 is None

    database.remove_item(item1)

    assert database.get_count(Test1) == 1
    assert len(database.get_items(Test1)) == 1

    assert database.get_item(Test1, col1=4) is None
    assert database.get_item(Test1, col1=-4) == item2

    item2.col2 = "Test string"

    database.save_item(item2)

    assert database.get_item(Test1, col1=-4).col2 == "Test string"
