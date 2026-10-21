"""Класс Student и функции работы с коллекцией студентов."""

from typing import Any

from models.entity import Entity, next_id
from utils import same_name


class Student(Entity):
    """Студент: имя и направление подготовки."""

    def __init__(self, student_id: int, name: str, specialty: str) -> None:
        """Создаёт студента."""
        super().__init__(student_id)
        self.name = name
        self.specialty = specialty

    def matches(self, query: str) -> bool:
        """Проверяет, содержит ли имя или специальность строку поиска."""
        query = query.lower()
        return query in self.name.lower() or query in self.specialty.lower()

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные студента для сохранения в JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "specialty": self.specialty,
        }

    def __str__(self) -> str:
        """Возвращает строку вида «Анна (аналитика)»."""
        return f"{self.name} ({self.specialty})"


def find_student(students: list[Student], name: str) -> Student | None:
    """Ищет студента по имени без учёта регистра."""
    for student in students:
        if same_name(student.name, name):
            return student
    return None


def find_student_by_id(
    students: list[Student],
    student_id: int,
) -> Student | None:
    """Ищет студента по идентификатору."""
    for student in students:
        if student.id == student_id:
            return student
    return None


def add_student(
    students: list[Student],
    name: str,
    specialty: str,
) -> Student | None:
    """Создаёт студента и добавляет его в коллекцию.

    Возвращает None, если имя пустое или такой студент уже есть.
    """
    name = name.strip()
    if not name or find_student(students, name) is not None:
        return None
    student = Student(next_id(students), name, specialty.strip())
    students.append(student)
    return student


def remove_student(students: list[Student], name: str) -> Student | None:
    """Удаляет студента из коллекции и возвращает его."""
    student = find_student(students, name)
    if student is not None:
        students.remove(student)
    return student


def search_students(students: list[Student], query: str) -> list[Student]:
    """Находит студентов по части имени или специальности."""
    return [student for student in students if student.matches(query)]


def filter_students_by_specialty(
    students: list[Student],
    specialty: str,
) -> list[Student]:
    """Отбирает студентов с указанной специальностью."""
    wanted = specialty.strip().casefold()
    return [
        student
        for student in students
        if student.specialty.casefold() == wanted
    ]


def sort_students(students: list[Student]) -> list[Student]:
    """Сортирует студентов по имени."""
    return sorted(students, key=lambda student: student.name.lower())


def student_statistics(students: list[Student]) -> dict[str, Any]:
    """Возвращает статистику по специальностям."""
    specialties: dict[str, int] = {}
    for student in students:
        specialties[student.specialty] = (
            specialties.get(student.specialty, 0) + 1
        )
    return {"total": len(students), "by_specialty": specialties}
