from typing import Any

from models.entity import Entity, next_id
from models.projects import Project, get_or_create_project
from models.roles import Role
from models.students import Student
from utils import same_name


# Membership Связывает студента с ролью
class Membership:
    # __init__ Задаёт участника и его роль
    def __init__(self, student: Student, role: Role | None = None) -> None:
        self.student = student
        self.role = role

    # assign_role Назначает роль участнику
    def assign_role(self, role: Role) -> None:
        self.role = role

    # to_dict Возвращает идентификаторы студента и роли
    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student.id,
            "role_id": self.role.id if self.role is not None else None,
        }

    # __str__ Описывает участника и его роль
    def __str__(self) -> str:
        role = self.role.name if self.role is not None else "не назначена"
        return f"{self.student.name} — {self.student.specialty}, роль: {role}"


# Team Хранит проект и состав команды
class Team(Entity):

    MIN_SIZE = 3
    MAX_SIZE = 5

    # __init__ Создаёт команду без участников
    def __init__(self, team_id: int, name: str, project: Project) -> None:
        super().__init__(team_id)
        self.name = name
        self.project = project
        self._members: list[Membership] = []

    # members Возвращает кортеж участников
    @property
    def members(self) -> tuple[Membership, ...]:
        return tuple(self._members)

    # find_member Ищет студента в составе команды
    def find_member(self, student: Student) -> Membership | None:
        for member in self._members:
            if member.student.id == student.id:
                return member
        return None

    # has_student Проверяет участие студента
    def has_student(self, student: Student) -> bool:
        return self.find_member(student) is not None

    # is_full Проверяет заполненность команды
    def is_full(self) -> bool:
        return len(self._members) >= self.MAX_SIZE

    # add_member Добавляет студента, если есть место и он ещё не в команде
    def add_member(self, student: Student, role: Role | None = None) -> bool:
        if self.has_student(student) or self.is_full():
            return False
        self._members.append(Membership(student, role))
        return True

    # remove_member Удаляет студента из команды
    def remove_member(self, student: Student) -> bool:
        member = self.find_member(student)
        if member is None:
            return False
        self._members.remove(member)
        return True

    # assign_role Назначает роль студенту в команде
    def assign_role(self, student: Student, role: Role) -> bool:
        member = self.find_member(student)
        if member is None:
            return False
        member.assign_role(role)
        return True

    # matches Ищет совпадение по названию или проекту
    def matches(self, query: str) -> bool:
        query = query.lower()
        return (
            query in self.name.lower()
            or query in self.project.title.lower()
        )

    # readiness Считает готовность по составу и ролям
    def readiness(self) -> tuple[int, str]:
        members_count = len(self._members)
        if members_count == 0:
            return 0, "Команда пока пуста"

        assigned_roles = sum(
            member.role is not None for member in self._members
        )
        percent = int(assigned_roles / max(members_count, self.MIN_SIZE) * 100)
        if members_count < self.MIN_SIZE:
            return percent, f"Нужно не менее {self.MIN_SIZE} участников"
        if assigned_roles < members_count:
            return percent, "Нужно назначить роли"
        return percent, "Команда готова к работе"

    # readiness_percent Возвращает процент готовности
    @property
    def readiness_percent(self) -> int:
        return self.readiness()[0]

    # readiness_message Возвращает сообщение о готовности
    @property
    def readiness_message(self) -> str:
        return self.readiness()[1]

    # to_dict Возвращает данные команды для JSON
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project.id,
            "members": [member.to_dict() for member in self._members],
        }

    # __str__ Описывает состав и готовность команды
    def __str__(self) -> str:
        percent, message = self.readiness()
        return (
            f"{self.name}: {self.project}; "
            f"участников: {len(self._members)}/{self.MAX_SIZE}; "
            f"готовность: {percent}% ({message})"
        )


# find_team Ищет команду по названию без учёта регистра
def find_team(teams: list[Team], name: str) -> Team | None:
    for team in teams:
        if same_name(team.name, name):
            return team
    return None


# find_team_by_id Ищет команду по идентификатору
def find_team_by_id(teams: list[Team], team_id: int) -> Team | None:
    for team in teams:
        if team.id == team_id:
            return team
    return None


# create_team Создаёт команду для проекта
def create_team(
    teams: list[Team],
    projects: list[Project],
    name: str,
    project_title: str,
) -> Team | None:
    name = name.strip()
    if not name or find_team(teams, name) is not None:
        return None
    project = get_or_create_project(projects, project_title)
    team = Team(next_id(teams), name, project)
    teams.append(team)
    return team


# remove_team Удаляет команду по названию
def remove_team(teams: list[Team], name: str) -> bool:
    team = find_team(teams, name)
    if team is None:
        return False
    teams.remove(team)
    return True


# find_student_team Ищет команду студента
def find_student_team(teams: list[Team], student: Student) -> Team | None:
    for team in teams:
        if team.has_student(student):
            return team
    return None


# join_team Добавляет студента с проверкой ограничений
def join_team(teams: list[Team], team: Team, student: Student) -> None:
    current_team = find_student_team(teams, student)
    if current_team is not None:
        raise ValueError(
            f"Студент уже состоит в команде «{current_team.name}»."
        )
    if team.is_full():
        raise ValueError(
            f"Команда заполнена: максимум {Team.MAX_SIZE} участников."
        )
    team.add_member(student)


# remove_student_from_teams Удаляет студента из всех команд
def remove_student_from_teams(teams: list[Team], student: Student) -> bool:
    removed = False
    for team in teams:
        removed = team.remove_member(student) or removed
    return removed


# search_teams Ищет команды по названию или проекту
def search_teams(teams: list[Team], query: str) -> list[Team]:
    return [team for team in teams if team.matches(query)]


# filter_incomplete_teams Отбирает неготовые команды
def filter_incomplete_teams(teams: list[Team]) -> list[Team]:
    return [team for team in teams if team.readiness()[0] < 100]


# sort_teams Сортирует команды по названию
def sort_teams(teams: list[Team]) -> list[Team]:
    return sorted(teams, key=lambda team: team.name.lower())
