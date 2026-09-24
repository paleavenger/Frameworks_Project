from datetime import date


def add_student_to_team(team: dict, student_name: str, specialty: str) -> bool:
    """Добавляет студента в команду и возвращает результат операции."""
    if student_name in team["students"]:
        return False

    team["students"][student_name] = {
        "specialty": specialty,
        "role": "не назначена",
    }
    return True


def assign_role(team: dict, student_name: str, role: str) -> bool:
    """Назначает роль участнику команды."""
    if student_name not in team["students"]:
        return False

    team["students"][student_name]["role"] = role
    return True


def calculate_team_readiness(team: dict) -> tuple[int, str]:
    """Оценивает готовность команды по числу студентов и ролей."""
    students_count = len(team["students"])
    assigned_roles = sum(
        1
        for student in team["students"].values()
        if student["role"] != "не назначена"
    )

    if students_count >= 3 and assigned_roles == students_count:
        return 100, "Команда готова к работе"
    if students_count > 0:
        return int(assigned_roles / students_count * 100), "Нужно назначить роли"
    return 0, "Команда пока пуста"


def main() -> None:
    """Демонстрирует основные операции программы."""
    team = {
        "name": "Команда Альфа",
        "project": "Электронный журнал посещаемости",
        "created_at": date.today().isoformat(),
        "students": {},
    }

    add_student_to_team(team, "Анна", "аналитика")
    add_student_to_team(team, "Борис", "разработка")
    add_student_to_team(team, "Вера", "тестирование")

    assign_role(team, "Анна", "аналитик")
    assign_role(team, "Борис", "разработчик")
    assign_role(team, "Вера", "тестировщик")

    readiness, message = calculate_team_readiness(team)
    print(f"Проект: {team['project']}")
    print(f"Команда: {team['name']} ({team['created_at']})")
    print(f"Участников: {len(team['students'])}")
    print(f"Готовность: {readiness}% — {message}")


if __name__ == "__main__":
    main()
