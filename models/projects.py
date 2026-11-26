from typing import Any

from models.entity import Entity, next_id
from utils import same_name


# Project Представляет учебный проект
class Project(Entity):
    # __init__ Задаёт идентификатор и название
    def __init__(self, project_id: int, title: str) -> None:
        super().__init__(project_id)
        self.title = title

    # to_dict Возвращает данные проекта для JSON
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title}

    # __str__ Возвращает название проекта
    def __str__(self) -> str:
        return self.title


# find_project Ищет проект по названию без учёта регистра
def find_project(projects: list[Project], title: str) -> Project | None:
    for project in projects:
        if same_name(project.title, title):
            return project
    return None


# find_project_by_id Ищет проект по идентификатору
def find_project_by_id(
    projects: list[Project],
    project_id: int,
) -> Project | None:
    for project in projects:
        if project.id == project_id:
            return project
    return None


# get_or_create_project Находит или создаёт проект
def get_or_create_project(projects: list[Project], title: str) -> Project:
    project = find_project(projects, title)
    if project is None:
        project = Project(next_id(projects), title.strip())
        projects.append(project)
    return project
