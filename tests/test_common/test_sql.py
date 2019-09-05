
import pytest

import spidertools.common as tutils


def test_empty_cursor():
    cursor = tutils.sql.EmptyCursor()

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
    database = tutils.GenericDatabase("", -1, "notauser", "", "talos_data", {}, connect=False)

    assert database.is_connected() is False, "Empty database considered connected"
    assert database.raw_exec("SELECT * FROM admins") == list(), "raw_exec didn't return empty fetchall"
    assert database.commit() is False, "Database committed despite not existing?"
    assert database.execute("SELECT * FROM admins WHERE id=%s", [12345678]) is None,\
        "Database execution returned unexpected result"
