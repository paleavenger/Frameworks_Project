import os
import sys
from io import StringIO
from pathlib import Path
from shutil import copyfile

import django
import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import setup_test_environment

sys.path.insert(0, str(Path(__file__).parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teamproject.settings")
django.setup()
setup_test_environment()

import storage  # noqa: E402
from db import database  # noqa: E402
from db.import_json import import_all  # noqa: E402
from models.projects import Project  # noqa: E402
from models.roles import default_roles  # noqa: E402
from models.students import Student  # noqa: E402
from models.teams import Team  # noqa: E402


# data_dir Готовит временные данные и базу SQLite
@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "teams.sqlite")
    students = [
        Student(1, "Анна", "аналитика"),
        Student(2, "Борис", "разработка"),
        Student(3, "Вера", "тестирование"),
        Student(4, "Глеб", "разработка"),
    ]
    roles = default_roles()
    project = Project(1, "Журнал")
    team = Team(1, "Альфа", project)
    team.add_member(students[0], roles[0])
    storage.save_entities("students.json", students)
    storage.save_entities("projects.json", [project])
    storage.save_entities("roles.json", roles)
    storage.save_entities("teams.json", [team])

    database.init_db()
    conn = database.get_connection()
    try:
        import_all(conn, storage.load_data())
    finally:
        conn.close()
    return tmp_path


# run_sql Возвращает функцию записи в тестовую базу
@pytest.fixture
def run_sql(data_dir):
    def run(query: str, params=()) -> None:
        conn = database.get_connection()
        try:
            conn.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    return run


# django_schema Применяет миграции к тестовой базе
@pytest.fixture(scope="session")
def django_schema(tmp_path_factory):
    path = tmp_path_factory.mktemp("django_schema") / "db.sqlite3"
    connection.close()
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(connection.settings_dict, "NAME", path)
        try:
            call_command("migrate", verbosity=0)
        finally:
            connection.close()
    return path


# orm_database Готовит тестовую базу Django с данными ПР7
@pytest.fixture
def orm_database(django_schema, data_dir, monkeypatch):
    path = data_dir / "db.sqlite3"
    copyfile(django_schema, path)
    monkeypatch.setitem(connection.settings_dict, "NAME", path)
    try:
        call_command(
            "import_pr7", source=data_dir / "teams.sqlite", stdout=StringIO(),
        )
        yield path
    finally:
        connection.close()
