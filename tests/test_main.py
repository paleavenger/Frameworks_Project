"""Тесты пунктов консольного меню."""

import json
from typing import Any

import pytest

import main
from storage import AppData


@pytest.fixture
def run(monkeypatch, capsys, data_dir):
    """Запускает меню с заданными ответами и возвращает вывод."""

    def runner(*answers: str) -> str:
        replies = iter([*answers, "0"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))
        main.main()
        return capsys.readouterr().out

    return runner


def saved(data_dir, filename: str) -> list[dict[str, Any]]:
    """Читает сохранённый JSON-файл."""
    return json.loads((data_dir / filename).read_text(encoding="utf-8"))


def saved_members(data_dir, team_index: int = 0) -> list[dict[str, Any]]:
    return saved(data_dir, "teams.json")[team_index]["members"]


def test_menu_1_add_student(run, data_dir) -> None:
    out = run("1", "Дарья", "дизайн", "1", "дарья", "дизайн")
    assert "Добавлено." in out
    assert "Такой студент уже есть." in out
    assert saved(data_dir, "students.json")[-1] == {
        "id": 5,
        "name": "Дарья",
        "specialty": "дизайн",
    }


def test_menu_2_remove_student_everywhere(run, data_dir) -> None:
    out = run("2", "анна", "2", "анна")
    assert "Студент удалён." in out
    assert "Студент не найден." in out
    assert all(s["name"] != "Анна" for s in saved(data_dir, "students.json"))
    assert saved_members(data_dir) == []


def test_menu_3_show_students(run) -> None:
    out = run("3")
    assert "- Анна (аналитика)" in out
    assert "- Глеб (разработка)" in out


def test_menu_4_find_students(run) -> None:
    out = run("4", "разраб")
    assert "- Борис (разработка)" in out
    assert "Анна" not in out


def test_menu_5_filter_by_specialty(run) -> None:
    out = run("5", "разработка", "5", "дизайн")
    assert "- Борис" in out and "- Глеб" in out
    assert "Анна" not in out
    assert out.count("Список студентов пуст.") == 1


def test_menu_6_statistics(run) -> None:
    out = run("6")
    assert "Всего студентов: 4" in out
    assert "- разработка: 2" in out


def test_menu_7_create_team(run, data_dir) -> None:
    out = run("7", "Бета", "Сайт", "7", "бета", "Сайт")
    assert "Команда создана." in out
    assert "Такая команда уже есть." in out
    teams = saved(data_dir, "teams.json")
    projects = saved(data_dir, "projects.json")
    assert teams[-1]["name"] == "Бета"
    assert {"id": 2, "title": "Сайт"} in projects
    assert teams[-1]["project_id"] == 2


def test_menu_7_team_reuses_existing_project(run, data_dir) -> None:
    run("7", "Бета", "журнал")
    assert len(saved(data_dir, "projects.json")) == 1
    assert saved(data_dir, "teams.json")[-1]["project_id"] == 1


def test_menu_8_remove_team(run, data_dir) -> None:
    out = run("8", "альфа", "8", "альфа")
    assert "Команда удалена." in out
    assert "Команда не найдена." in out
    assert saved(data_dir, "teams.json") == []


def test_menu_9_add_student_to_team(run, data_dir) -> None:
    out = run("9", "Альфа", "Борис")
    assert "Студент добавлен." in out
    assert {"student_id": 2, "role_id": None} in saved_members(data_dir)


def test_menu_9_student_belongs_to_one_team_only(run, data_dir) -> None:
    out = run("7", "Бета", "Сайт", "9", "Бета", "Анна")
    assert "Студент уже состоит в команде «Альфа»." in out
    assert saved_members(data_dir, 1) == []


def test_menu_9_team_capacity(run, data_dir) -> None:
    answers = ["1", "Дарья", "дизайн", "1", "Егор", "дизайн"]
    for name in ("Борис", "Вера", "Глеб", "Дарья", "Егор"):
        answers += ["9", "Альфа", name]
    out = run(*answers)
    assert "Команда заполнена: максимум 5 участников." in out
    members = saved_members(data_dir)
    assert len(members) == 5
    assert all(member["student_id"] != 6 for member in members)


def test_menu_9_unknown_team_or_student(run) -> None:
    out = run("9", "Нет", "Борис", "9", "Альфа", "Нет")
    assert out.count("Команда или студент не найдены.") == 2


def test_menu_10_assign_role(run, data_dir) -> None:
    out = run(
        "9", "Альфа", "Борис",
        "10", "Альфа", "борис", "волшебник",
        "10", "Альфа", "борис", "Разработчик",
        "10", "Альфа", "Вера", "дизайнер",
        "10", "Нет", "Борис", "дизайнер",
    )
    assert "Неизвестная роль." in out
    assert "Роль назначена." in out
    assert "Студент не найден в команде." in out
    assert "Команда не найдена." in out
    assert {"student_id": 2, "role_id": 2} in saved_members(data_dir)


def test_menu_11_remove_student_from_team(run, data_dir) -> None:
    out = run(
        "11", "Альфа", "анна",
        "11", "Альфа", "анна",
        "11", "Нет", "Анна",
    )
    assert "Студент удалён." in out
    assert "Студент не найден в команде." in out
    assert "Команда не найдена." in out
    assert saved_members(data_dir) == []


def test_menu_12_show_teams_with_members(run) -> None:
    out = run("12")
    assert "- Альфа: Журнал; участников: 1/5" in out
    assert "Анна — аналитика, роль: аналитик" in out


def test_menu_13_find_teams(run) -> None:
    assert "- Альфа" in run("13", "журн")
    assert "Альфа" not in run("13", "сайт")


def test_menu_14_show_incomplete_teams(run) -> None:
    out = run("14")
    assert "- Альфа" in out
    assert "Нужно не менее 3 участников" in out


def test_menu_15_show_projects(run) -> None:
    out = run("15")
    assert "- Журнал: команд — 1" in out


def test_invalid_menu_input_does_not_crash(run) -> None:
    out = run("abc", "99", "")
    assert "нужно ввести целое число" in out
    assert "Введите число от 0 до 15." in out


def test_broken_json_does_not_crash_or_overwrite(capsys, data_dir) -> None:
    (data_dir / "students.json").write_text("{", encoding="utf-8")
    main.main()
    assert "Ошибка данных" in capsys.readouterr().out
    assert (data_dir / "students.json").read_text(encoding="utf-8") == "{"


def test_invalid_structure_does_not_crash(capsys, data_dir) -> None:
    (data_dir / "teams.json").write_text(
        '[{"id": 1, "name": "А", "project_id": 99, "members": []}]',
        encoding="utf-8",
    )
    main.main()
    assert "Не найден проект команды" in capsys.readouterr().out


def test_save_error_does_not_crash(run, monkeypatch) -> None:
    def fail(data: AppData) -> None:
        raise RuntimeError("нет доступа")

    monkeypatch.setattr(main, "save_data", fail)
    out = run("3")
    assert "Ошибка сохранения: нет доступа" in out
    assert "Данные сохранены." not in out
