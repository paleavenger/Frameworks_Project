from models.students import (
    Student,
    add_student,
    filter_students_by_specialty,
    find_student,
    find_student_by_id,
    remove_student,
    search_students,
    sort_students,
    student_statistics,
)


def make_students() -> list[Student]:
    return [
        Student(1, "Вера", "тестирование"),
        Student(2, "Анна", "аналитика"),
        Student(3, "Борис", "аналитика"),
    ]


def test_student_creation_and_str() -> None:
    student = Student(1, "Анна", "аналитика")
    assert student.id == 1
    assert student.name == "Анна"
    assert student.specialty == "аналитика"
    assert str(student) == "Анна (аналитика)"
    assert student.to_dict() == {
        "id": 1,
        "name": "Анна",
        "specialty": "аналитика",
    }


def test_student_matches() -> None:
    student = Student(1, "Анна", "аналитика")
    assert student.matches("анн")
    assert student.matches("АНАЛИТ")
    assert not student.matches("разработка")


def test_add_student() -> None:
    students: list[Student] = []
    student = add_student(students, " Иван ", " разработка ")
    assert student is not None
    assert (student.id, student.name, student.specialty) == (
        1,
        "Иван",
        "разработка",
    )
    assert students == [student]
    assert add_student(students, "Дарья", "дизайн").id == 2


def test_add_student_rejects_duplicates_and_empty_names() -> None:
    students = [Student(1, "Иван", "разработка")]
    assert add_student(students, "иван", "дизайн") is None
    assert add_student(students, "  ", "дизайн") is None
    assert len(students) == 1


def test_find_student() -> None:
    students = make_students()
    assert find_student(students, " анна ") is students[1]
    assert find_student(students, "Нет") is None
    assert find_student_by_id(students, 3) is students[2]
    assert find_student_by_id(students, 99) is None


def test_remove_student() -> None:
    students = make_students()
    removed = remove_student(students, "анна")
    assert removed is not None and removed.name == "Анна"
    assert len(students) == 2
    assert remove_student(students, "Анна") is None


def test_search_filter_sort() -> None:
    students = make_students()
    assert [s.name for s in search_students(students, "аналит")] == [
        "Анна",
        "Борис",
    ]
    assert [
        s.name for s in filter_students_by_specialty(students, " Аналитика ")
    ] == ["Анна", "Борис"]
    assert filter_students_by_specialty(students, "аналит") == []
    assert [s.name for s in sort_students(students)] == [
        "Анна",
        "Борис",
        "Вера",
    ]


def test_student_statistics() -> None:
    assert student_statistics(make_students()) == {
        "total": 3,
        "by_specialty": {"тестирование": 1, "аналитика": 2},
    }
    assert student_statistics([]) == {"total": 0, "by_specialty": {}}
