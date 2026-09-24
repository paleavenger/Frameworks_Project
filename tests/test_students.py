from students import add_student, find_students, sort_students


def test_add_student() -> None:
    students: dict[str, dict[str, str]] = {}
    assert add_student(students, "Иван", "разработка") is True
    assert add_student(students, "Иван", "разработка") is False


def test_find_students() -> None:
    students = {"Анна": {"specialty": "аналитика"}}
    assert find_students(students, "аналит") == students


def test_sort_students() -> None:
    students = {
        "Вера": {"specialty": "тестирование"},
        "Анна": {"specialty": "аналитика"},
    }
    assert [name for name, _ in sort_students(students)] == ["Анна", "Вера"]
