from typing import Any

from models.entity import Entity, next_id
from utils import same_name


# Student Хранит имя и специальность студента
class Student(Entity):
    # __init__ Задаёт данные студента
    def __init__(self, student_id: int, name: str, specialty: str) -> None:
        super().__init__(student_id)
        self.name = name
        self.specialty = specialty

    # matches Ищет совпадение по имени или специальности
    def matches(self, query: str) -> bool:
        query = query.lower()
        return query in self.name.lower() or query in self.specialty.lower()

    # to_dict Возвращает данные студента для JSON
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "specialty": self.specialty,
        }

    # __str__ Возвращает имя и специальность
    def __str__(self) -> str:
        return f"{self.name} ({self.specialty})"


# find_student Ищет студента по имени без учёта регистра
def find_student(students: list[Student], name: str) -> Student | None:
    for student in students:
        if same_name(student.name, name):
            return student
    return None


# find_student_by_id Ищет студента по идентификатору
def find_student_by_id(
    students: list[Student],
    student_id: int,
) -> Student | None:
    for student in students:
        if student.id == student_id:
            return student
    return None


# add_student Добавляет студента в список
def add_student(
    students: list[Student],
    name: str,
    specialty: str,
) -> Student | None:
    name = name.strip()
    if not name or find_student(students, name) is not None:
        return None
    student = Student(next_id(students), name, specialty.strip())
    students.append(student)
    return student


# remove_student Удаляет студента по имени
def remove_student(students: list[Student], name: str) -> Student | None:
    student = find_student(students, name)
    if student is not None:
        students.remove(student)
    return student


# search_students Ищет студентов по имени или специальности
def search_students(students: list[Student], query: str) -> list[Student]:
    return [student for student in students if student.matches(query)]


# filter_students_by_specialty Отбирает студентов по специальности
def filter_students_by_specialty(
    students: list[Student],
    specialty: str,
) -> list[Student]:
    wanted = specialty.strip().casefold()
    return [
        student
        for student in students
        if student.specialty.casefold() == wanted
    ]


# sort_students Сортирует студентов по имени
def sort_students(students: list[Student]) -> list[Student]:
    return sorted(students, key=lambda student: student.name.lower())


# student_statistics Считает студентов по специальностям
def student_statistics(students: list[Student]) -> dict[str, Any]:
    specialties: dict[str, int] = {}
    for student in students:
        specialties[student.specialty] = (
            specialties.get(student.specialty, 0) + 1
        )
    return {"total": len(students), "by_specialty": specialties}
