import sqlite3
import sys

from db.database import get_connection, init_db
from storage import AppData, load_data


# clear_tables Очищает таблицы перед импортом
def clear_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM team_members")
    conn.execute("DELETE FROM teams")
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM projects")
    conn.execute("DELETE FROM roles")


# import_roles Переносит роли
def import_roles(conn: sqlite3.Connection, data: AppData) -> None:
    conn.executemany(
        "INSERT INTO roles (id, name) VALUES (?, ?)",
        [(role.id, role.name) for role in data.roles],
    )


# import_projects Переносит проекты
def import_projects(conn: sqlite3.Connection, data: AppData) -> None:
    conn.executemany(
        "INSERT INTO projects (id, title) VALUES (?, ?)",
        [(project.id, project.title) for project in data.projects],
    )


# import_students Переносит студентов
def import_students(conn: sqlite3.Connection, data: AppData) -> None:
    conn.executemany(
        "INSERT INTO students (id, name, specialty) VALUES (?, ?, ?)",
        [
            (student.id, student.name, student.specialty)
            for student in data.students
        ],
    )


# import_teams Переносит команды и участников
def import_teams(conn: sqlite3.Connection, data: AppData) -> None:
    conn.executemany(
        "INSERT INTO teams (id, name, project_id) VALUES (?, ?, ?)",
        [(team.id, team.name, team.project.id) for team in data.teams],
    )
    conn.executemany(
        "INSERT INTO team_members (team_id, student_id, role_id) "
        "VALUES (?, ?, ?)",
        [
            (
                team.id,
                member.student.id,
                member.role.id if member.role is not None else None,
            )
            for team in data.teams
            for member in team.members
        ],
    )


# import_all Импортирует JSON в одной транзакции
def import_all(conn: sqlite3.Connection, data: AppData) -> None:
    try:
        clear_tables(conn)
        import_roles(conn, data)
        import_projects(conn, data)
        import_students(conn, data)
        import_teams(conn, data)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# main Запускает импорт из JSON в SQLite
def main() -> int:
    try:
        data = load_data()
    except (RuntimeError, ValueError) as error:
        print(f"Ошибка в JSON-файлах: {error}")
        return 1

    init_db()
    conn = get_connection()
    try:
        import_all(conn, data)
        print(
            "Импортировано: "
            f"студентов — {len(data.students)}, "
            f"проектов — {len(data.projects)}, "
            f"ролей — {len(data.roles)}, "
            f"команд — {len(data.teams)}."
        )
    except sqlite3.Error as error:
        print(f"Ошибка записи в базу данных: {error}")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
