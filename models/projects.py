"""Класс Project и функции работы с коллекцией проектов."""

from typing import Any

from models.entity import Entity, next_id
from utils import same_name


class Project(Entity):
    """Учебный проект, над которым работает команда."""

    def __init__(self, project_id: int, title: str) -> None:
        """Создаёт проект."""
        super().__init__(project_id)
        self.title = title

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные проекта для сохранения в JSON."""
        return {"id": self.id, "title": self.title}

    def __str__(self) -> str:
        """Возвращает название проекта."""
        return self.title


def find_project(projects: list[Project], title: str) -> Project | None:
    """Ищет проект по названию без учёта регистра."""
    for project in projects:
        if same_name(project.title, title):
            return project
    return None


def find_project_by_id(
    projects: list[Project],
    project_id: int,
) -> Project | None:
    """Ищет проект по идентификатору."""
    for project in projects:
        if project.id == project_id:
            return project
    return None


def get_or_create_project(projects: list[Project], title: str) -> Project:
    """Возвращает существующий проект или создаёт новый."""
    project = find_project(projects, title)
    if project is None:
        project = Project(next_id(projects), title.strip())
        projects.append(project)
    return project
