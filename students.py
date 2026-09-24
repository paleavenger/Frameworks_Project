"""Операции со студентами."""

from typing import Any


def add_student(
    students: dict[str, dict[str, str]],
    name: str,
    specialty: str,
) -> bool:
    """Добавляет студента, если такого имени ещё нет."""
    if not name or name in students:
        return False
    students[name] = {"specialty": specialty}
    return True


def remove_student(students: dict[str, dict[str, str]], name: str) -> bool:
    """Удаляет студента по имени."""
    if name not in students:
        return False
    del students[name]
    return True


def find_students(
    students: dict[str, dict[str, str]],
    query: str,
) -> dict[str, dict[str, str]]:
    """Находит студентов по части имени или специальности."""
    query_lower = query.lower()
    return {
        name: data
        for name, data in students.items()
        if query_lower in name.lower()
        or query_lower in data["specialty"].lower()
    }


def sort_students(
    students: dict[str, dict[str, str]],
) -> list[tuple[str, dict[str, str]]]:
    """Сортирует студентов по имени."""
    return sorted(students.items(), key=lambda item: item[0].lower())


def student_statistics(students: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Возвращает статистику по специальностям."""
    specialties: dict[str, int] = {}
    for student in students.values():
        specialty = student["specialty"]
        specialties[specialty] = specialties.get(specialty, 0) + 1
    return {"total": len(students), "by_specialty": specialties}
