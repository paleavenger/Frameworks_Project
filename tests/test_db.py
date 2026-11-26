import re
import sqlite3
from pathlib import Path

import pytest

import storage
from db import database, import_json
from models.projects import Project
from models.roles import default_roles
from models.students import Student
from models.teams import Team

QUERIES_PATH = Path(database.BASE_DIR) / "sql" / "queries.sql"


@pytest.fixture
def conn(data_dir):
    connection = database.get_connection()
    yield connection
    connection.close()


def scalar(conn: sqlite3.Connection, query: str, params=()) -> object:
    return conn.execute(query, params).fetchone()[0]


def test_tables_are_created(conn) -> None:
    names = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {
        "students", "projects", "roles", "teams", "team_members",
    } <= names


def test_foreign_keys_are_declared(conn) -> None:
    def targets(table: str) -> dict[str, str]:
        rows = conn.execute(f"PRAGMA foreign_key_list({table})")
        return {row["from"]: row["table"] for row in rows}

    assert targets("teams") == {"project_id": "projects"}
    assert targets("team_members") == {
        "team_id": "teams",
        "student_id": "students",
        "role_id": "roles",
    }


def test_connection_settings(conn) -> None:
    assert scalar(conn, "PRAGMA foreign_keys") == 1
    assert conn.row_factory is sqlite3.Row
    row = conn.execute("SELECT id, title FROM projects").fetchone()
    assert row["title"] == "Журнал"


def test_init_db_can_be_run_twice(data_dir) -> None:
    database.init_db()
    database.init_db()
    conn = database.get_connection()
    try:
        assert scalar(conn, "SELECT COUNT(*) FROM students") == 4
    finally:
        conn.close()


def test_missing_database_is_not_created_silently(
    data_dir, monkeypatch
) -> None:
    path = data_dir / "other.sqlite"
    monkeypatch.setattr(database, "DB_PATH", path)
    with pytest.raises(FileNotFoundError):
        database.get_connection()
    assert not path.exists()


def test_fetch_helpers_use_parameters(data_dir) -> None:
    row = database.fetch_one("SELECT name FROM students WHERE id = ?", [2])
    assert row["name"] == "Борис"
    assert database.fetch_one(
        "SELECT name FROM students WHERE id = ?", [999]
    ) is None
    rows = database.fetch_all(
        "SELECT id FROM students WHERE specialty = ?", ["разработка"]
    )
    assert [row["id"] for row in rows] == [2, 4]


def test_foreign_key_rejects_unknown_student(conn) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO team_members (team_id, student_id) VALUES (1, 999)"
        )


def test_foreign_key_rejects_unknown_project(conn) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO teams (id, name, project_id) VALUES (9, 'Х', 999)"
        )


def test_student_cannot_be_in_two_teams(conn) -> None:
    conn.execute("INSERT INTO teams (id, name, project_id) VALUES (2, 'Б', 1)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO team_members (team_id, student_id) VALUES (2, 1)"
        )


def test_team_is_limited_to_max_size(conn) -> None:
    for number in range(10, 14):
        conn.execute(
            "INSERT INTO students (id, name) VALUES (?, 'С')", [number]
        )
        conn.execute(
            "INSERT INTO team_members (team_id, student_id) VALUES (1, ?)",
            [number],
        )
    assert scalar(
        conn, "SELECT COUNT(*) FROM team_members WHERE team_id = 1"
    ) == Team.MAX_SIZE
    conn.execute("INSERT INTO students (id, name) VALUES (20, 'Лишний')")
    with pytest.raises(sqlite3.IntegrityError, match="не более 5"):
        conn.execute(
            "INSERT INTO team_members (team_id, student_id) VALUES (1, 20)"
        )


def test_moving_member_to_full_team_is_rejected(conn) -> None:
    conn.execute("INSERT INTO teams (id, name, project_id) VALUES (2, 'Б', 1)")
    conn.execute("INSERT INTO students (id, name) VALUES (30, 'Новый')")
    conn.execute(
        "INSERT INTO team_members (id, team_id, student_id) "
        "VALUES (100, 2, 30)"
    )
    for number in range(10, 14):
        conn.execute(
            "INSERT INTO students (id, name) VALUES (?, 'С')", [number]
        )
        conn.execute(
            "INSERT INTO team_members (team_id, student_id) VALUES (1, ?)",
            [number],
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE team_members SET team_id = 1 WHERE id = 100")


def test_deleting_team_removes_its_members(conn) -> None:
    conn.execute("DELETE FROM teams WHERE id = 1")
    assert scalar(conn, "SELECT COUNT(*) FROM team_members") == 0
    assert scalar(conn, "SELECT COUNT(*) FROM students") == 4


@pytest.mark.parametrize("members, with_roles", [
    (0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 0), (3, 2), (3, 3),
    (4, 3), (4, 4), (5, 5),
])
def test_team_overview_matches_python_readiness(
    data_dir, members: int, with_roles: int
) -> None:
    roles = default_roles()
    students = [Student(n, f"С{n}", "x") for n in range(1, members + 1)]
    project = Project(1, "П")
    team = Team(1, "К", project)
    for number, student in enumerate(students):
        team.add_member(student, roles[0] if number < with_roles else None)
    storage.save_entities("students.json", students)
    storage.save_entities("projects.json", [project])
    storage.save_entities("roles.json", roles)
    storage.save_entities("teams.json", [team])
    assert import_json.main() == 0

    row = database.fetch_one(
        "SELECT readiness_percent, readiness_message, members_count "
        "FROM team_overview WHERE id = 1"
    )
    percent, message = team.readiness()
    assert row["readiness_percent"] == percent
    assert row["readiness_message"] == message
    assert row["members_count"] == members


def test_import_counts_match_json(conn, data_dir) -> None:
    data = storage.load_data()
    assert scalar(conn, "SELECT COUNT(*) FROM students") == len(data.students)
    assert scalar(conn, "SELECT COUNT(*) FROM projects") == len(data.projects)
    assert scalar(conn, "SELECT COUNT(*) FROM roles") == len(data.roles)
    assert scalar(conn, "SELECT COUNT(*) FROM teams") == len(data.teams)
    assert scalar(conn, "SELECT COUNT(*) FROM team_members") == 1


def test_import_keeps_ids_and_missing_roles(data_dir) -> None:
    team = storage.load_data().teams[0]
    team.add_member(storage.load_data().students[1])
    storage.save_entities("teams.json", [team])
    assert import_json.main() == 0
    rows = database.fetch_all(
        "SELECT student_id, role_id FROM team_members ORDER BY student_id"
    )
    assert [tuple(row) for row in rows] == [(1, 1), (2, None)]
    assert database.fetch_one(
        "SELECT name FROM students WHERE id = 3"
    )["name"] == "Вера"


def test_repeated_import_does_not_duplicate_rows(data_dir) -> None:
    assert import_json.main() == 0
    assert import_json.main() == 0
    assert database.fetch_one("SELECT COUNT(*) AS n FROM students")["n"] == 4
    assert database.fetch_one("SELECT COUNT(*) AS n FROM roles")["n"] == 4


def test_import_replaces_database_content(data_dir, run_sql) -> None:
    run_sql("UPDATE students SET name = 'Изменено' WHERE id = 1")
    assert import_json.main() == 0
    assert database.fetch_one(
        "SELECT name FROM students WHERE id = 1"
    )["name"] == "Анна"


def test_import_creates_database_file(data_dir) -> None:
    (data_dir / "teams.sqlite").unlink()
    assert import_json.main() == 0
    assert (data_dir / "teams.sqlite").is_file()


def test_failed_import_rolls_back(data_dir, monkeypatch) -> None:
    def fail(conn, data) -> None:
        raise sqlite3.OperationalError("сбой")

    monkeypatch.setattr(import_json, "import_teams", fail)
    conn = database.get_connection()
    try:
        with pytest.raises(sqlite3.OperationalError):
            import_json.import_all(conn, storage.load_data())
    finally:
        conn.close()
    assert database.fetch_one("SELECT COUNT(*) AS n FROM students")["n"] == 4
    assert database.fetch_one(
        "SELECT COUNT(*) AS n FROM team_members"
    )["n"] == 1


def test_import_reports_broken_json(data_dir, capsys) -> None:
    (data_dir / "students.json").write_text("{", encoding="utf-8")
    assert import_json.main() == 1
    assert "Ошибка в JSON-файлах" in capsys.readouterr().out
    assert database.fetch_one("SELECT COUNT(*) AS n FROM students")["n"] == 4


# read_queries Разбивает SQL-файл на запросы
def read_queries() -> list[str]:
    queries: list[str] = []
    buffer = ""
    for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines(True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            queries.append(buffer.strip())
            buffer = ""
    assert not buffer.strip()
    return queries


# code Возвращает SQL без комментариев в верхнем регистре
def code(query: str) -> str:
    return "\n".join(
        line for line in query.splitlines()
        if not line.lstrip().startswith("--")
    ).upper()


def test_queries_file_has_enough_queries() -> None:
    queries = read_queries()
    assert len(queries) >= 10
    for query in queries:
        assert re.search(r"^-- \d+\. ", query, re.MULTILINE), query


@pytest.mark.parametrize("keyword, minimum", [
    ("SELECT", 10),
    ("WHERE", 2),
    ("JOIN", 2),
    ("COUNT(", 2),
    ("GROUP BY", 2),
    ("HAVING", 1),
    ("LIMIT", 1),
])
def test_queries_cover_required_kinds(keyword: str, minimum: int) -> None:
    used = sum(keyword in code(query) for query in read_queries())
    assert used >= minimum


def test_all_queries_run(conn) -> None:
    for query in read_queries():
        conn.execute(query).fetchall()


def test_query_results_on_fixture_data(conn) -> None:
    results = {
        number: conn.execute(query).fetchall()
        for number, query in enumerate(read_queries(), start=1)
    }
    names = [row["name"] for row in results[1]]
    assert names == ["Анна", "Борис", "Вера", "Глеб"]
    assert [row["name"] for row in results[8]] == ["Борис", "Вера", "Глеб"]
    assert [row["id"] for row in results[10]] == [1]
    assert results[18][0]["students_count"] == 4
    assert results[19][0]["free_students_count"] == 3
    assert results[20][0]["without_role_count"] == 0
    assert results[25] == []
    assert [row["name"] for row in results[26]] == ["Альфа"]
