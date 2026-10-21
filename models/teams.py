"""Классы Membership и Team, функции работы с коллекцией команд."""

from typing import Any

from models.entity import Entity, next_id
from models.projects import Project, get_or_create_project
from models.roles import Role
from models.students import Student
from utils import same_name


class Membership:
    """Участие студента в команде: ссылка на студента и его роль."""

    def __init__(self, student: Student, role: Role | None = None) -> None:
        """Создаёт участие; роль может быть ещё не назначена."""
        self.student = student
        self.role = role

    def assign_role(self, role: Role) -> None:
        """Назначает роль участнику."""
        self.role = role

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные участия; ссылки заменяются идентификаторами."""
        return {
            "student_id": self.student.id,
            "role_id": self.role.id if self.role is not None else None,
        }

    def __str__(self) -> str:
        """Возвращает описание участника и его роли."""
        role = self.role.name if self.role is not None else "не назначена"
        return f"{self.student.name} — {self.student.specialty}, роль: {role}"


class Team(Entity):
    """Учебная проектная команда.

    Хранит ссылку на проект и список участников. Состав меняется только
    через методы класса, чтобы соблюдались ограничения на размер команды.
    """

    MIN_SIZE = 3
    MAX_SIZE = 5

    def __init__(self, team_id: int, name: str, project: Project) -> None:
        """Создаёт команду без участников."""
        super().__init__(team_id)
        self.name = name
        self.project = project
        self._members: list[Membership] = []

    @property
    def members(self) -> tuple[Membership, ...]:
        """Возвращает участников команды (только для чтения)."""
        return tuple(self._members)

    def find_member(self, student: Student) -> Membership | None:
        """Ищет участие студента в команде."""
        for member in self._members:
            if member.student.id == student.id:
                return member
        return None

    def has_student(self, student: Student) -> bool:
        """Проверяет, что студент состоит в команде."""
        return self.find_member(student) is not None

    def is_full(self) -> bool:
        """Проверяет, что в команде нет свободных мест."""
        return len(self._members) >= self.MAX_SIZE

    def add_member(self, student: Student, role: Role | None = None) -> bool:
        """Добавляет студента в команду.

        Возвращает False, если студент уже в команде или она заполнена.
        """
        if self.has_student(student) or self.is_full():
            return False
        self._members.append(Membership(student, role))
        return True

    def remove_member(self, student: Student) -> bool:
        """Удаляет студента из команды."""
        member = self.find_member(student)
        if member is None:
            return False
        self._members.remove(member)
        return True

    def assign_role(self, student: Student, role: Role) -> bool:
        """Назначает роль участнику; False, если он не в команде."""
        member = self.find_member(student)
        if member is None:
            return False
        member.assign_role(role)
        return True

    def matches(self, query: str) -> bool:
        """Проверяет, содержит ли название или проект строку поиска."""
        query = query.lower()
        return (
            query in self.name.lower()
            or query in self.project.title.lower()
        )

    def readiness(self) -> tuple[int, str]:
        """Оценивает готовность команды по числу участников и ролей.

        Процент считается от большего из двух чисел: числа участников
        и минимального размера команды MIN_SIZE.
        """
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

    @property
    def readiness_percent(self) -> int:
        """Возвращает процент готовности команды."""
        return self.readiness()[0]

    @property
    def readiness_message(self) -> str:
        """Возвращает текстовый статус готовности команды."""
        return self.readiness()[1]

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные команды; проект заменяется идентификатором."""
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project.id,
            "members": [member.to_dict() for member in self._members],
        }

    def __str__(self) -> str:
        """Возвращает описание команды с процентом готовности."""
        percent, message = self.readiness()
        return (
            f"{self.name}: {self.project}; "
            f"участников: {len(self._members)}/{self.MAX_SIZE}; "
            f"готовность: {percent}% ({message})"
        )


def find_team(teams: list[Team], name: str) -> Team | None:
    """Ищет команду по названию без учёта регистра."""
    for team in teams:
        if same_name(team.name, name):
            return team
    return None


def find_team_by_id(teams: list[Team], team_id: int) -> Team | None:
    """Ищет команду по идентификатору."""
    for team in teams:
        if team.id == team_id:
            return team
    return None


def create_team(
    teams: list[Team],
    projects: list[Project],
    name: str,
    project_title: str,
) -> Team | None:
    """Создаёт команду и добавляет её в коллекцию.

    Проект находится по названию или создаётся. Возвращает None, если
    название пустое или такая команда уже есть.
    """
    name = name.strip()
    if not name or find_team(teams, name) is not None:
        return None
    project = get_or_create_project(projects, project_title)
    team = Team(next_id(teams), name, project)
    teams.append(team)
    return team


def remove_team(teams: list[Team], name: str) -> bool:
    """Удаляет команду по названию."""
    team = find_team(teams, name)
    if team is None:
        return False
    teams.remove(team)
    return True


def find_student_team(teams: list[Team], student: Student) -> Team | None:
    """Возвращает команду, в которой состоит студент."""
    for team in teams:
        if team.has_student(student):
            return team
    return None


def join_team(teams: list[Team], team: Team, student: Student) -> None:
    """Добавляет студента в команду с проверкой правил предметной области.

    Студент может состоять только в одной команде, а команда вмещает
    не более Team.MAX_SIZE участников. При нарушении выбрасывает ValueError.
    """
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


def remove_student_from_teams(teams: list[Team], student: Student) -> bool:
    """Удаляет студента из всех команд."""
    removed = False
    for team in teams:
        removed = team.remove_member(student) or removed
    return removed


def search_teams(teams: list[Team], query: str) -> list[Team]:
    """Находит команды по названию или проекту."""
    return [team for team in teams if team.matches(query)]


def filter_incomplete_teams(teams: list[Team]) -> list[Team]:
    """Отбирает команды, которые ещё не готовы к работе."""
    return [team for team in teams if team.readiness()[0] < 100]


def sort_teams(teams: list[Team]) -> list[Team]:
    """Сортирует команды по названию."""
    return sorted(teams, key=lambda team: team.name.lower())
