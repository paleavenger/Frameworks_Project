"""Операции с учебными командами."""

from typing import Any


def create_team(
    teams: dict[str, dict[str, Any]],
    name: str,
    project: str,
) -> bool:
    """Создаёт команду с пустым списком участников."""
    if not name or name in teams:
        return False
    teams[name] = {"project": project, "students": {}}
    return True


def add_student_to_team(
    team: dict[str, Any],
    student_name: str,
    specialty: str,
) -> bool:
    """Добавляет студента в команду и возвращает результат операции."""
    students = team["students"]
    if student_name in students:
        return False
    students[student_name] = {
        "specialty": specialty,
        "role": "не назначена",
    }
    return True


def assign_role(
    team: dict[str, Any],
    student_name: str,
    role: str,
) -> bool:
    """Назначает роль участнику команды."""
    if student_name not in team["students"]:
        return False
    team["students"][student_name]["role"] = role
    return True


def remove_student_from_team(
    team: dict[str, Any],
    student_name: str,
) -> bool:
    """Удаляет студента из команды."""
    if student_name not in team["students"]:
        return False
    del team["students"][student_name]
    return True


def calculate_team_readiness(team: dict[str, Any]) -> tuple[int, str]:
    """Оценивает готовность команды по числу участников и ролей."""
    students_count = len(team["students"])
    assigned_roles = sum(
        student["role"] != "не назначена"
        for student in team["students"].values()
    )
    if students_count >= 3 and assigned_roles == students_count:
        return 100, "Команда готова к работе"
    if students_count > 0:
        return (
            int(assigned_roles / students_count * 100),
            "Нужно назначить роли",
        )
    return 0, "Команда пока пуста"


def search_teams(
    teams: dict[str, dict[str, Any]],
    query: str,
) -> dict[str, dict[str, Any]]:
    """Находит команды по названию или проекту."""
    query_lower = query.lower()
    return {
        name: team
        for name, team in teams.items()
        if query_lower in name.lower()
        or query_lower in team["project"].lower()
    }


def sort_teams(
    teams: dict[str, dict[str, Any]],
) -> list[tuple[str, dict[str, Any]]]:
    """Сортирует команды по названию."""
    return sorted(teams.items(), key=lambda item: item[0].lower())
