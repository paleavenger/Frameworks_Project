import json

import pytest

import storage
from models.projects import Project
from models.roles import default_roles
from models.students import Student
from models.teams import Team


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return tmp_path


def write(data_dir, filename: str, content) -> None:
    (data_dir / filename).write_text(
        json.dumps(content, ensure_ascii=False), encoding="utf-8"
    )


def write_valid(data_dir) -> None:
    write(data_dir, "students.json", [
        {"id": 1, "name": "Анна", "specialty": "аналитика"},
        {"id": 2, "name": "Борис", "specialty": "разработка"},
    ])
    write(data_dir, "projects.json", [{"id": 1, "title": "Журнал"}])
    write(data_dir, "roles.json", [{"id": 1, "name": "аналитик"}])
    write(data_dir, "teams.json", [{
        "id": 1,
        "name": "Альфа",
        "project_id": 1,
        "members": [
            {"student_id": 1, "role_id": 1},
            {"student_id": 2, "role_id": None},
        ],
    }])


def load_everything():
    students = storage.load_students()
    projects = storage.load_projects()
    roles = storage.load_roles()
    return students, projects, roles, storage.load_teams(
        students, projects, roles
    )


def test_save_and_load_json(data_dir) -> None:
    storage.save_json("x.json", [{"id": 1, "name": "Анна"}])
    assert storage.load_json("x.json") == [{"id": 1, "name": "Анна"}]
    text = (data_dir / "x.json").read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert "Анна" in text
    assert not list(data_dir.glob("*.tmp"))


def test_load_missing_file_returns_empty_list(data_dir) -> None:
    assert storage.load_json("none.json") == []
    assert storage.load_students() == []


def test_load_broken_json_raises(data_dir) -> None:
    (data_dir / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(RuntimeError):
        storage.load_json("bad.json")


def test_load_wrong_structure_raises(data_dir) -> None:
    write(data_dir, "a.json", {"id": 1})
    write(data_dir, "b.json", [1, 2])
    for name in ("a.json", "b.json"):
        with pytest.raises(RuntimeError):
            storage.load_json(name)


def test_load_creates_linked_objects(data_dir) -> None:
    write_valid(data_dir)
    students, projects, roles, teams = load_everything()
    team = teams[0]
    assert team.project is projects[0]
    assert team.members[0].student is students[0]
    assert team.members[0].role is roles[0]
    assert team.members[1].role is None


def test_save_and_reload_roundtrip(data_dir) -> None:
    write_valid(data_dir)
    students, projects, roles, teams = load_everything()
    for filename, entities in (
        ("students.json", students),
        ("projects.json", projects),
        ("roles.json", roles),
        ("teams.json", teams),
    ):
        storage.save_entities(filename, entities)
    reloaded = load_everything()
    assert [t.to_dict() for t in reloaded[3]] == [t.to_dict() for t in teams]
    assert reloaded[0][1].name == "Борис"


def test_saved_team_contains_ids_not_objects(data_dir) -> None:
    student = Student(1, "Анна", "аналитика")
    team = Team(1, "Альфа", Project(7, "Журнал"))
    team.add_member(student, default_roles()[0])
    storage.save_entities("teams.json", [team])
    assert storage.load_json("teams.json") == [{
        "id": 1,
        "name": "Альфа",
        "project_id": 7,
        "members": [{"student_id": 1, "role_id": 1}],
    }]


def test_roles_default_when_file_missing(data_dir) -> None:
    assert [r.name for r in storage.load_roles()][0] == "аналитик"
    assert len(storage.load_roles()) == 4


@pytest.mark.parametrize("filename, content", [
    ("students.json", [{"id": 1, "name": "Анна"}]),
    ("students.json", [{"id": "1", "name": "Анна", "specialty": "x"}]),
    ("students.json", [{"id": True, "name": "Анна", "specialty": "x"}]),
    ("students.json", [
        {"id": 1, "name": "Анна", "specialty": "x"},
        {"id": 1, "name": "Борис", "specialty": "x"},
    ]),
    ("projects.json", [{"id": 1}]),
])
def test_invalid_records_raise_value_error(
    data_dir, filename: str, content
) -> None:
    write_valid(data_dir)
    write(data_dir, filename, content)
    with pytest.raises(ValueError):
        load_everything()


@pytest.mark.parametrize("team", [
    {"id": 1, "name": "А", "project_id": 99, "members": []},
    {"id": 1, "name": "А", "project_id": 1,
     "members": [{"student_id": 99, "role_id": None}]},
    {"id": 1, "name": "А", "project_id": 1,
     "members": [{"student_id": 1, "role_id": 99}]},
    {"id": 1, "name": "А", "project_id": 1,
     "members": [{"student_id": 1, "role_id": None},
                 {"student_id": 1, "role_id": None}]},
    {"id": 1, "name": "А", "project_id": 1, "members": ["Анна"]},
    {"id": 1, "name": "А", "project_id": 1},
])
def test_broken_references_raise_value_error(data_dir, team) -> None:
    write_valid(data_dir)
    write(data_dir, "teams.json", [team])
    with pytest.raises(ValueError):
        load_everything()


def test_student_in_two_teams_raises(data_dir) -> None:
    write_valid(data_dir)
    member = [{"student_id": 1, "role_id": None}]
    write(data_dir, "teams.json", [
        {"id": 1, "name": "А", "project_id": 1, "members": member},
        {"id": 2, "name": "Б", "project_id": 1, "members": member},
    ])
    with pytest.raises(ValueError, match="двух командах"):
        load_everything()


def test_oversized_team_raises(data_dir) -> None:
    write_valid(data_dir)
    write(data_dir, "students.json", [
        {"id": n, "name": f"С{n}", "specialty": "x"} for n in range(1, 8)
    ])
    members = [{"student_id": n, "role_id": None} for n in range(1, 8)]
    write(data_dir, "teams.json", [
        {"id": 1, "name": "А", "project_id": 1, "members": members},
    ])
    with pytest.raises(ValueError, match="переполнена"):
        load_everything()
