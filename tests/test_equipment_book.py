from estimate_project import equipment_book


class DummyCursor:
    def __init__(self, rows=None, rowcount=0):
        self.rows = rows or []
        self.rowcount = rowcount
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.rows


class DummyConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


def test_format_rate_handles_none_int_and_decimal():
    assert equipment_book._format_rate(None) == ""
    assert equipment_book._format_rate(10.0) == "10"
    assert equipment_book._format_rate(10.25) == "10.25"
    assert equipment_book._format_rate(10.50) == "10.5"


def test_fetch_equipment_from_postgresql_maps_rows(monkeypatch):
    rows = [
        ("Building Demo", "Excavator", 1200.0, 5000.0, 18000.0),
        (None, None, None, 3500.0, 10000.0),
    ]
    cursor = DummyCursor(rows=rows)
    conn = DummyConnection(cursor)

    monkeypatch.setattr(equipment_book, "get_db_connection", lambda: conn)

    result = equipment_book.fetch_equipment_from_postgresql("building", "exc")

    assert len(result) == 2
    assert result[0] == {
        "Project Type": "Building Demo",
        "Equipment": "Excavator",
        "Day": "1200",
        "Week": "5000",
        "Month": "18000",
    }
    assert result[1] == {
        "Project Type": "N/A",
        "Equipment": "",
        "Day": "",
        "Week": "3500",
        "Month": "10000",
    }

    assert len(cursor.executed) == 1
    query, params = cursor.executed[0]
    assert "WHERE" in query
    assert "project_type ILIKE %s" in query
    assert "equipment_name ILIKE %s" in query
    assert params == ["%building%", "%exc%"]


def test_fetch_equipment_from_postgresql_falls_back_to_sample(monkeypatch):
    def raise_connection_error():
        raise OSError("database unavailable")

    monkeypatch.setattr(equipment_book, "get_db_connection", raise_connection_error)
    monkeypatch.setattr(
        equipment_book,
        "_load_sample_equipment_rows",
        lambda: [
            ("Building Demo", "Excavator", "1200", "5000", "18000"),
            ("Interior Demolition", "Dust Extractor", "200", "700", "2100"),
        ],
    )

    result = equipment_book.fetch_equipment_from_postgresql("building", "exc")

    assert result == [
        {
            "Project Type": "Building Demo",
            "Equipment": "Excavator",
            "Day": "1200",
            "Week": "5000",
            "Month": "18000",
        }
    ]


def test_insert_equipment_to_postgresql_executes_insert_and_commits(monkeypatch):
    cursor = DummyCursor()
    conn = DummyConnection(cursor)
    monkeypatch.setattr(equipment_book, "get_db_connection", lambda: conn)

    equipment_book.insert_equipment_to_postgresql("House Demo", "Skid Steer", 300, 1000, 3200)

    assert len(cursor.executed) == 1
    query, params = cursor.executed[0]
    assert "INSERT INTO equipment" in query
    assert params == ("House Demo", "Skid Steer", 300, 1000, 3200)
    assert conn.committed is True


def test_insert_equipment_to_postgresql_raises_read_only_error_on_connection_failure(monkeypatch):
    def raise_connection_error():
        raise OSError("database unavailable")

    monkeypatch.setattr(equipment_book, "get_db_connection", raise_connection_error)

    try:
        equipment_book.insert_equipment_to_postgresql("House Demo", "Skid Steer", 300, 1000, 3200)
        assert False, "Expected RuntimeError to be raised"
    except RuntimeError as exc:
        assert "read-only" in str(exc).lower()


def test_update_equipment_in_postgresql_returns_updated_rows(monkeypatch):
    cursor = DummyCursor(rowcount=1)
    conn = DummyConnection(cursor)
    monkeypatch.setattr(equipment_book, "get_db_connection", lambda: conn)

    original_equipment = {
        "Project Type": "House Demo",
        "Equipment": "Skid Steer",
        "Day": 300.0,
        "Week": 1000.0,
        "Month": 3200.0,
    }
    updated_equipment = {
        "Project Type": "House Demo",
        "Equipment": "Skid Steer XL",
        "Day": 350.0,
        "Week": 1200.0,
        "Month": 3600.0,
    }

    updated_rows = equipment_book.update_equipment_in_postgresql(original_equipment, updated_equipment)

    assert updated_rows == 1
    assert len(cursor.executed) == 1
    query, params = cursor.executed[0]
    assert "UPDATE equipment" in query
    assert params[0:5] == ("House Demo", "Skid Steer XL", 350.0, 1200.0, 3600.0)
    assert params[5:10] == ("House Demo", "Skid Steer", 300.0, 1000.0, 3200.0)
    assert conn.committed is True


def test_delete_equipment_from_postgresql_returns_deleted_rows(monkeypatch):
    cursor = DummyCursor(rowcount=2)
    conn = DummyConnection(cursor)
    monkeypatch.setattr(equipment_book, "get_db_connection", lambda: conn)

    equipment_item = {
        "Project Type": "Building Demo",
        "Equipment": "Excavator",
        "Day": 1200.0,
        "Week": 5000.0,
        "Month": 18000.0,
    }

    deleted_rows = equipment_book.delete_equipment_from_postgresql(equipment_item)

    assert deleted_rows == 2
    assert len(cursor.executed) == 1
    query, params = cursor.executed[0]
    assert "DELETE FROM equipment" in query
    assert params == ("Building Demo", "Excavator", 1200.0, 5000.0, 18000.0)
    assert conn.committed is True


def test_equipment_book_initial_state():
    book = equipment_book.EquipmentBook()

    assert book.filtered_equipment == []
    assert book.total_equipment_cost == 0
    assert book.FONT == "Times New Roman"
