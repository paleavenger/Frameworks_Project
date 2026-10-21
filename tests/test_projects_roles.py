from models.projects import (
    Project,
    find_project,
    find_project_by_id,
    get_or_create_project,
)
from models.roles import Role, default_roles, find_role, find_role_by_id


def test_project_creation_and_str() -> None:
    project = Project(1, "Журнал")
    assert project.id == 1
    assert project.title == "Журнал"
    assert str(project) == "Журнал"
    assert project.to_dict() == {"id": 1, "title": "Журнал"}


def test_find_project() -> None:
    projects = [Project(1, "Журнал")]
    assert find_project(projects, " журнал ") is projects[0]
    assert find_project(projects, "Сайт") is None
    assert find_project_by_id(projects, 1) is projects[0]
    assert find_project_by_id(projects, 2) is None


def test_get_or_create_project() -> None:
    projects: list[Project] = []
    first = get_or_create_project(projects, " Журнал ")
    assert first.title == "Журнал"
    assert get_or_create_project(projects, "журнал") is first
    assert get_or_create_project(projects, "Сайт").id == 2
    assert len(projects) == 2


def test_role_creation_and_str() -> None:
    role = Role(1, "аналитик")
    assert str(role) == "аналитик"
    assert role.to_dict() == {"id": 1, "name": "аналитик"}


def test_default_roles_and_search() -> None:
    roles = default_roles()
    assert [role.name for role in roles] == [
        "аналитик",
        "разработчик",
        "дизайнер",
        "тестировщик",
    ]
    assert find_role(roles, " Дизайнер ") is roles[2]
    assert find_role(roles, "король") is None
    assert find_role_by_id(roles, 4) is roles[3]
    assert find_role_by_id(roles, 9) is None
