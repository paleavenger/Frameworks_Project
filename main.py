from typing import Callable

from models.projects import Project
from models.roles import find_role
from models.students import (
    Student,
    add_student,
    filter_students_by_specialty,
    find_student,
    remove_student,
    search_students,
    sort_students,
    student_statistics,
)
from models.teams import (
    Team,
    create_team,
    filter_incomplete_teams,
    find_team,
    join_team,
    remove_student_from_teams,
    remove_team,
    search_teams,
    sort_teams,
)
from storage import AppData, load_data, save_data
from utils import input_int, input_non_empty

Menu = dict[int, tuple[str, Callable[[], None]]]


# save_all Сохраняет данные и выводит ошибку записи
def save_all(data: AppData) -> bool:
    try:
        save_data(data)
    except RuntimeError as error:
        print(f"Ошибка сохранения: {error}")
        return False
    return True


# print_students Выводит список студентов
def print_students(students: list[Student]) -> None:
    if not students:
        print("Список студентов пуст.")
    for student in sort_students(students):
        print(f"- {student}")


# print_statistics Выводит статистику по специальностям
def print_statistics(students: list[Student]) -> None:
    statistics = student_statistics(students)
    print(f"Всего студентов: {statistics['total']}")
    for specialty, count in sorted(statistics["by_specialty"].items()):
        print(f"- {specialty}: {count}")


# print_teams Выводит команды и их состав
def print_teams(teams: list[Team]) -> None:
    if not teams:
        print("Список команд пуст.")
    for team in sort_teams(teams):
        print(f"- {team}")
        for member in team.members:
            print(f"    {member}")


# print_projects Выводит проекты и число их команд
def print_projects(projects: list[Project], teams: list[Team]) -> None:
    if not projects:
        print("Список проектов пуст.")
    for project in sorted(projects, key=lambda item: item.title.lower()):
        count = sum(team.project is project for team in teams)
        print(f"- {project}: команд — {count}")


# add_student_action Добавляет студента через меню
def add_student_action(data: AppData) -> None:
    name = input_non_empty("Имя: ")
    specialty = input_non_empty("Специальность: ")
    student = add_student(data.students, name, specialty)
    print("Добавлено." if student else "Такой студент уже есть.")


# remove_student_action Удаляет студента из списка и команд
def remove_student_action(data: AppData) -> None:
    name = input_non_empty("Имя студента: ")
    student = remove_student(data.students, name)
    if student is None:
        print("Студент не найден.")
        return
    remove_student_from_teams(data.teams, student)
    print("Студент удалён.")


# find_student_action Выводит результаты поиска студентов
def find_student_action(data: AppData) -> None:
    query = input_non_empty("Поиск: ")
    print_students(search_students(data.students, query))


# filter_students_action Выводит студентов выбранной специальности
def filter_students_action(data: AppData) -> None:
    specialty = input_non_empty("Специальность: ")
    print_students(filter_students_by_specialty(data.students, specialty))


# create_team_action Создаёт команду через меню
def create_team_action(data: AppData) -> None:
    name = input_non_empty("Название команды: ")
    project_title = input_non_empty("Проект: ")
    team = create_team(data.teams, data.projects, name, project_title)
    print("Команда создана." if team else "Такая команда уже есть.")


# remove_team_action Удаляет команду через меню
def remove_team_action(data: AppData) -> None:
    name = input_non_empty("Название команды: ")
    result = remove_team(data.teams, name)
    print("Команда удалена." if result else "Команда не найдена.")


# add_to_team_action Добавляет студента в выбранную команду
def add_to_team_action(data: AppData) -> None:
    team = find_team(data.teams, input_non_empty("Команда: "))
    student = find_student(data.students, input_non_empty("Студент: "))
    if team is None or student is None:
        print("Команда или студент не найдены.")
        return
    try:
        join_team(data.teams, team, student)
    except ValueError as error:
        print(error)
        return
    print("Студент добавлен.")


# assign_role_action Назначает роль в команде
def assign_role_action(data: AppData) -> None:
    team_name = input_non_empty("Команда: ")
    student_name = input_non_empty("Студент: ")
    role_names = ", ".join(role.name for role in data.roles)
    role = find_role(data.roles, input_non_empty(f"Роль ({role_names}): "))
    team = find_team(data.teams, team_name)
    if team is None:
        print("Команда не найдена.")
        return
    if role is None:
        print(f"Неизвестная роль. Доступные роли: {role_names}.")
        return
    student = find_student(data.students, student_name)
    if student is None or not team.assign_role(student, role):
        print("Студент не найден в команде.")
        return
    print("Роль назначена.")


# remove_from_team_action Удаляет студента из команды
def remove_from_team_action(data: AppData) -> None:
    team = find_team(data.teams, input_non_empty("Команда: "))
    student = find_student(data.students, input_non_empty("Студент: "))
    if team is None:
        print("Команда не найдена.")
        return
    if student is None or not team.remove_member(student):
        print("Студент не найден в команде.")
        return
    print("Студент удалён.")


# find_team_action Выводит результаты поиска команд
def find_team_action(data: AppData) -> None:
    query = input_non_empty("Поиск: ")
    print_teams(search_teams(data.teams, query))


# build_menu Связывает пункты меню с действиями
def build_menu(data: AppData) -> Menu:
    return {
        1: ("Добавить студента", lambda: add_student_action(data)),
        2: ("Удалить студента", lambda: remove_student_action(data)),
        3: ("Показать студентов", lambda: print_students(data.students)),
        4: ("Найти студентов", lambda: find_student_action(data)),
        5: (
            "Отобрать студентов по специальности",
            lambda: filter_students_action(data),
        ),
        6: ("Показать статистику", lambda: print_statistics(data.students)),
        7: ("Создать команду", lambda: create_team_action(data)),
        8: ("Удалить команду", lambda: remove_team_action(data)),
        9: (
            "Добавить студента в команду",
            lambda: add_to_team_action(data),
        ),
        10: ("Назначить роль", lambda: assign_role_action(data)),
        11: (
            "Удалить студента из команды",
            lambda: remove_from_team_action(data),
        ),
        12: ("Показать команды", lambda: print_teams(data.teams)),
        13: ("Найти команды", lambda: find_team_action(data)),
        14: (
            "Показать неготовые команды",
            lambda: print_teams(filter_incomplete_teams(data.teams)),
        ),
        15: (
            "Показать проекты",
            lambda: print_projects(data.projects, data.teams),
        ),
    }


# show_menu Выводит пункты меню
def show_menu(menu: Menu) -> None:
    print("\n=== Система управления учебными проектными командами ===")
    for number, (title, _) in menu.items():
        print(f"{number}. {title}")
    print("0. Выход")


# main Запускает консольное меню
def main() -> None:
    try:
        data = load_data()
    except (RuntimeError, ValueError) as error:
        print(f"Ошибка данных: {error}")
        print("Исправьте файлы в каталоге data/ и запустите программу снова.")
        return

    menu = build_menu(data)
    try:
        while True:
            show_menu(menu)
            choice = input_int("Выберите пункт: ", 0, len(menu))
            if choice == 0:
                break
            menu[choice][1]()
            save_all(data)
    except (EOFError, KeyboardInterrupt):
        print()
    if save_all(data):
        print("Данные сохранены.")


if __name__ == "__main__":
    main()
