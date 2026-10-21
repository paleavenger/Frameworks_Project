"""Общие настройки и фикстуры тестов."""

import os
import sys
from pathlib import Path

import django
import pytest
from django.test.utils import setup_test_environment

sys.path.insert(0, str(Path(__file__).parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teamproject.settings")
django.setup()
setup_test_environment()

import storage  # noqa: E402
from models.projects import Project  # noqa: E402
from models.roles import default_roles  # noqa: E402
from models.students import Student  # noqa: E402
from models.teams import Team  # noqa: E402


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Подменяет каталог данных на временный с тестовыми файлами."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
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
    return tmp_path
