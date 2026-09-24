"""Консольное приложение TeamProject Manager."""

from typing import Any

from storage import load_json, save_json
from students import (
    add_student,
    find_students,
    remove_student,
    sort_students,
    student_statistics,
)
from teams import (
    add_student_to_team,
    assign_role,
    calculate_team_readiness,
    create_team,
    remove_student_from_team,
    search_teams,
    sort_teams,
)
from utils import input_int, input_non_empty


def print_students(students: dict[str, dict[str, str]]) -> None:
    """Печатает список студентов."""
    for name, data in sort_students(students):
        print(f"- {name}: {data['specialty']}")


def print_teams(teams: dict[str, dict[str, Any]]) -> None:
    """Печатает список команд и участников."""
    for name, team in sort_teams(teams):
        readiness, message = calculate_team_readiness(team)
        print(
            f"- {name}: {team['project']}; "
            f"участников: {len(team['students'])}; "
            f"готовность: {readiness}% ({message})"
        )


def save_all(students: dict[str, Any], teams: dict[str, Any]) -> None:
    """Сохраняет студентов и команды."""
    save_json("students.json", students)
    save_json("teams.json", teams)


def show_menu() -> None:
    """Печатает меню приложения."""
    print(
        "\n1. Добавить студента\n"
        "2. Удалить студента\n"
        "3. Найти студентов\n"
        "4. Показать статистику\n"
        "5. Создать команду\n"
        "6. Добавить студента в команду\n"
        "7. Назначить роль\n"
        "8. Удалить студента из команды\n"
        "9. Показать команды\n"
        "10. Найти команды\n"
        "0. Выход"
    )


def main() -> None:
    """Запускает основной цикл консольного меню."""
    students = load_json("students.json", {})
    teams = load_json("teams.json", {})
    actions = {
        1: lambda: add_student_action(students),
        2: lambda: remove_student_action(students, teams),
        3: lambda: find_student_action(students),
        4: lambda: print(student_statistics(students)),
        5: lambda: create_team_action(teams),
        6: lambda: add_to_team_action(students, teams),
        7: lambda: assign_role_action(teams),
        8: lambda: remove_from_team_action(teams),
        9: lambda: print_teams(teams),
        10: lambda: find_team_action(teams),
    }
    while True:
        show_menu()
        choice = input_int("Выберите пункт: ", 0, 10)
        if choice == 0:
            save_all(students, teams)
            print("Данные сохранены.")
            return
        actions[choice]()
        save_all(students, teams)


def add_student_action(students: dict[str, Any]) -> None:
    """Обрабатывает добавление студента."""
    name = input_non_empty("Имя: ")
    specialty = input_non_empty("Специальность: ")
    result = add_student(students, name, specialty)
    print("Добавлено." if result else "Такой студент уже есть.")


def remove_student_action(
    students: dict[str, Any],
    teams: dict[str, Any],
) -> None:
    """Удаляет студента из справочника и всех команд."""
    name = input_non_empty("Имя студента: ")
    removed = remove_student(students, name)
    for team in teams.values():
        remove_student_from_team(team, name)
    print("Студент удалён." if removed else "Студент не найден.")


def find_student_action(students: dict[str, Any]) -> None:
    """Печатает результаты поиска студентов."""
    query = input_non_empty("Поиск: ")
    print_students(find_students(students, query))


def create_team_action(teams: dict[str, Any]) -> None:
    """Обрабатывает создание команды."""
    name = input_non_empty("Название команды: ")
    project = input_non_empty("Проект: ")
    result = create_team(teams, name, project)
    print("Команда создана." if result else "Такая команда уже есть.")


def add_to_team_action(
    students: dict[str, Any],
    teams: dict[str, Any],
) -> None:
    """Добавляет существующего студента в команду."""
    team_name = input_non_empty("Команда: ")
    student_name = input_non_empty("Студент: ")
    if team_name not in teams or student_name not in students:
        print("Команда или студент не найдены.")
        return
    specialty = students[student_name]["specialty"]
    result = add_student_to_team(teams[team_name], student_name, specialty)
    print("Студент добавлен." if result else "Студент уже в команде.")


def assign_role_action(teams: dict[str, Any]) -> None:
    """Назначает роль участнику команды."""
    team_name = input_non_empty("Команда: ")
    student_name = input_non_empty("Студент: ")
    role = input_non_empty("Роль: ")
    if team_name not in teams:
        print("Команда не найдена.")
        return
    result = assign_role(teams[team_name], student_name, role)
    print("Роль назначена." if result else "Студент не найден в команде.")


def remove_from_team_action(teams: dict[str, Any]) -> None:
    """Удаляет участника из команды."""
    team_name = input_non_empty("Команда: ")
    student_name = input_non_empty("Студент: ")
    if team_name not in teams:
        print("Команда не найдена.")
        return
    result = remove_student_from_team(teams[team_name], student_name)
    print("Студент удалён." if result else "Студент не найден в команде.")


def find_team_action(teams: dict[str, Any]) -> None:
    """Печатает результаты поиска команд."""
    query = input_non_empty("Поиск: ")
    print_teams(search_teams(teams, query))


if __name__ == "__main__":
    main()
