import pytest

from models.projects import Project
from models.roles import Role
from models.students import Student
from models.teams import (
    Membership,
    Team,
    create_team,
    filter_incomplete_teams,
    find_student_team,
    find_team,
    find_team_by_id,
    join_team,
    remove_student_from_teams,
    remove_team,
    search_teams,
    sort_teams,
)

ANALYST = Role(1, "аналитик")
DEVELOPER = Role(2, "разработчик")
TESTER = Role(3, "тестировщик")


def make_students(count: int) -> list[Student]:
    return [
        Student(number, f"Студент {number}", "x")
        for number in range(1, count + 1)
    ]


def make_team(name: str = "Альфа") -> Team:
    return Team(1, name, Project(1, "Журнал"))


def test_membership() -> None:
    student = Student(1, "Анна", "аналитика")
    member = Membership(student)
    assert member.student is student
    assert member.role is None
    assert str(member) == "Анна — аналитика, роль: не назначена"
    member.assign_role(ANALYST)
    assert member.role is ANALYST
    assert str(member).endswith("роль: аналитик")
    assert member.to_dict() == {"student_id": 1, "role_id": 1}
    assert Membership(student).to_dict() == {"student_id": 1, "role_id": None}


def test_team_holds_references_to_objects() -> None:
    project = Project(1, "Журнал")
    team = Team(1, "Альфа", project)
    student = Student(1, "Анна", "аналитика")
    assert team.add_member(student, ANALYST) is True
    assert team.project is project
    assert team.members[0].student is student
    assert team.members[0].role is ANALYST
    assert team.to_dict() == {
        "id": 1,
        "name": "Альфа",
        "project_id": 1,
        "members": [{"student_id": 1, "role_id": 1}],
    }


def test_members_are_read_only_view() -> None:
    team = make_team()
    team.add_member(make_students(1)[0])
    assert isinstance(team.members, tuple)
    assert not hasattr(team.members, "append")


def test_add_member_rejects_duplicate() -> None:
    team = make_team()
    student = make_students(1)[0]
    assert team.add_member(student) is True
    assert team.add_member(student) is False
    assert len(team.members) == 1


def test_team_capacity() -> None:
    team = make_team()
    students = make_students(Team.MAX_SIZE + 1)
    for student in students[:-1]:
        assert team.is_full() is False
        assert team.add_member(student) is True
    assert team.is_full() is True
    assert team.add_member(students[-1]) is False
    assert len(team.members) == Team.MAX_SIZE


def test_remove_member_and_assign_role() -> None:
    team = make_team()
    anna, boris = make_students(2)
    team.add_member(anna)
    assert team.assign_role(anna, DEVELOPER) is True
    assert team.find_member(anna).role is DEVELOPER
    assert team.assign_role(boris, DEVELOPER) is False
    assert team.remove_member(anna) is True
    assert team.remove_member(anna) is False
    assert team.has_student(anna) is False


def test_readiness_ready_team() -> None:
    team = make_team()
    for student, role in zip(make_students(3), (ANALYST, DEVELOPER, TESTER)):
        team.add_member(student, role)
    assert team.readiness() == (100, "Команда готова к работе")


def test_readiness_empty_team() -> None:
    assert make_team().readiness() == (0, "Команда пока пуста")


def test_readiness_small_team_is_not_ready() -> None:
    team = make_team()
    for student in make_students(2):
        team.add_member(student, ANALYST)
    assert team.readiness() == (66, "Нужно не менее 3 участников")


def test_readiness_missing_roles() -> None:
    team = make_team()
    first, second, third = make_students(3)
    team.add_member(first, ANALYST)
    team.add_member(second)
    team.add_member(third)
    assert team.readiness() == (33, "Нужно назначить роли")


def test_team_str() -> None:
    team = make_team()
    assert str(team) == (
        "Альфа: Журнал; участников: 0/5; готовность: 0% (Команда пока пуста)"
    )


def test_create_and_find_team() -> None:
    teams: list[Team] = []
    projects: list[Project] = []
    team = create_team(teams, projects, " Альфа ", "Журнал")
    assert team is not None
    assert team.name == "Альфа"
    assert team.project is projects[0]
    assert find_team(teams, "альфа") is team
    assert find_team_by_id(teams, team.id) is team
    assert find_team_by_id(teams, 99) is None


def test_create_team_rejects_duplicate_without_new_project() -> None:
    teams: list[Team] = []
    projects: list[Project] = []
    create_team(teams, projects, "Альфа", "Журнал")
    assert create_team(teams, projects, " альфа ", "Сайт") is None
    assert create_team(teams, projects, "  ", "Сайт") is None
    assert len(teams) == 1
    assert len(projects) == 1


def test_teams_share_existing_project() -> None:
    teams: list[Team] = []
    projects: list[Project] = []
    first = create_team(teams, projects, "Альфа", "Журнал")
    second = create_team(teams, projects, "Бета", "журнал")
    assert first.project is second.project
    assert len(projects) == 1


def test_remove_team() -> None:
    teams = [make_team()]
    assert remove_team(teams, "альфа") is True
    assert teams == []
    assert remove_team(teams, "Альфа") is False


def test_join_team_enforces_one_team_per_student() -> None:
    alpha = make_team("Альфа")
    beta = Team(2, "Бета", Project(2, "Сайт"))
    teams = [alpha, beta]
    student = make_students(1)[0]
    join_team(teams, alpha, student)
    assert find_student_team(teams, student) is alpha
    with pytest.raises(ValueError, match="уже состоит в команде «Альфа»"):
        join_team(teams, beta, student)
    assert beta.members == ()


def test_join_team_enforces_capacity() -> None:
    team = make_team()
    teams = [team]
    students = make_students(Team.MAX_SIZE + 1)
    for student in students[:-1]:
        join_team(teams, team, student)
    with pytest.raises(ValueError, match="Команда заполнена"):
        join_team(teams, team, students[-1])
    assert len(team.members) == Team.MAX_SIZE


def test_remove_student_from_teams() -> None:
    team = make_team()
    student = make_students(1)[0]
    team.add_member(student)
    assert remove_student_from_teams([team], student) is True
    assert remove_student_from_teams([team], student) is False
    assert team.members == ()


def test_search_filter_sort_teams() -> None:
    alpha = Team(1, "Альфа", Project(1, "Журнал"))
    beta = Team(2, "бета", Project(2, "Сайт"))
    for student, role in zip(make_students(3), (ANALYST, DEVELOPER, TESTER)):
        alpha.add_member(student, role)
    teams = [beta, alpha]
    assert search_teams(teams, "журн") == [alpha]
    assert search_teams(teams, "xyz") == []
    assert filter_incomplete_teams(teams) == [beta]
    assert sort_teams(teams) == [alpha, beta]
