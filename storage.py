"""Работа с JSON-хранилищем: преобразование данных в объекты и обратно."""

import json
from pathlib import Path
from typing import Any

from models.entity import Entity
from models.projects import Project, find_project_by_id
from models.roles import Role, default_roles, find_role_by_id
from models.students import Student, find_student_by_id
from models.teams import Team, find_student_team


DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str) -> list[dict[str, Any]]:
    """Загружает список записей из JSON-файла.

    Если файла нет, возвращает пустой список. Повреждённый файл или
    неверная структура приводят к RuntimeError.
    """
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Не удалось прочитать {path}: {error}") from error

    if not isinstance(data, list) or not all(
        isinstance(item, dict) for item in data
    ):
        raise RuntimeError(f"Файл {path} должен содержать список объектов")
    return data


def save_json(filename: str, data: list[dict[str, Any]]) -> None:
    """Сохраняет список записей в JSON-файл."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    temp_path = path.with_name(path.name + ".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        temp_path.replace(path)
    except OSError as error:
        raise RuntimeError(f"Не удалось записать {path}: {error}") from error


def _field(data: dict[str, Any], key: str, kind: type) -> Any:
    """Возвращает поле записи, проверяя его наличие и тип."""
    value = data.get(key)
    if not isinstance(value, kind) or isinstance(value, bool):
        raise ValueError(f"Некорректное поле «{key}» в записи {data}")
    return value


def _check_unique_ids(entities: list[Entity], label: str) -> None:
    """Проверяет, что идентификаторы сущностей не повторяются."""
    ids = [entity.id for entity in entities]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Повторяющиеся идентификаторы: {label}")


def load_students() -> list[Student]:
    """Загружает студентов из students.json."""
    students = [
        Student(
            _field(item, "id", int),
            _field(item, "name", str),
            _field(item, "specialty", str),
        )
        for item in load_json("students.json")
    ]
    _check_unique_ids(students, "студенты")
    return students


def load_projects() -> list[Project]:
    """Загружает проекты из projects.json."""
    projects = [
        Project(_field(item, "id", int), _field(item, "title", str))
        for item in load_json("projects.json")
    ]
    _check_unique_ids(projects, "проекты")
    return projects


def load_roles() -> list[Role]:
    """Загружает роли из roles.json; без файла берёт стандартный набор."""
    roles = [
        Role(_field(item, "id", int), _field(item, "name", str))
        for item in load_json("roles.json")
    ]
    _check_unique_ids(roles, "роли")
    return roles or default_roles()


def _build_team(
    data: dict[str, Any],
    students: list[Student],
    projects: list[Project],
    roles: list[Role],
) -> Team:
    """Создаёт команду из записи, связывая её с найденными объектами."""
    project = find_project_by_id(projects, _field(data, "project_id", int))
    if project is None:
        raise ValueError(f"Не найден проект команды: {data}")
    team = Team(_field(data, "id", int), _field(data, "name", str), project)

    for item in _field(data, "members", list):
        if not isinstance(item, dict):
            raise ValueError(f"Некорректный участник команды «{team.name}»")
        student_id = _field(item, "student_id", int)
        student = find_student_by_id(students, student_id)
        if student is None:
            raise ValueError(f"Не найден студент в команде «{team.name}»")
        role = None
        if item.get("role_id") is not None:
            role = find_role_by_id(roles, _field(item, "role_id", int))
            if role is None:
                raise ValueError(f"Не найдена роль в команде «{team.name}»")
        if not team.add_member(student, role):
            raise ValueError(
                f"Студент «{student.name}» повторяется в команде "
                f"«{team.name}» или команда переполнена"
            )
    return team


def load_teams(
    students: list[Student],
    projects: list[Project],
    roles: list[Role],
) -> list[Team]:
    """Загружает команды из teams.json и проверяет правила предметной области.

    Если студент, проект или роль не найдены либо студент состоит в двух
    командах, выбрасывается ValueError.
    """
    teams: list[Team] = []
    for item in load_json("teams.json"):
        team = _build_team(item, students, projects, roles)
        for member in team.members:
            other = find_student_team(teams, member.student)
            if other is not None:
                raise ValueError(
                    f"Студент «{member.student.name}» состоит в двух "
                    f"командах: «{other.name}» и «{team.name}»"
                )
        teams.append(team)
    _check_unique_ids(teams, "команды")
    return teams


def save_entities(filename: str, entities: list[Entity]) -> None:
    """Сохраняет коллекцию сущностей в JSON-файл."""
    save_json(filename, [entity.to_dict() for entity in entities])


class AppData:
    """Коллекции объектов приложения."""

    def __init__(
        self,
        students: list[Student],
        projects: list[Project],
        roles: list[Role],
        teams: list[Team],
    ) -> None:
        """Сохраняет коллекции студентов, проектов, ролей и команд."""
        self.students = students
        self.projects = projects
        self.roles = roles
        self.teams = teams


def load_data() -> AppData:
    """Загружает все данные; при ошибке выбрасывает RuntimeError/ValueError."""
    students = load_students()
    projects = load_projects()
    roles = load_roles()
    teams = load_teams(students, projects, roles)
    return AppData(students, projects, roles, teams)


def save_data(data: AppData) -> None:
    """Сохраняет все коллекции; при ошибке записи выбрасывает RuntimeError."""
    save_entities("students.json", data.students)
    save_entities("projects.json", data.projects)
    save_entities("roles.json", data.roles)
    save_entities("teams.json", data.teams)
