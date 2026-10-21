"""Класс Role и функции работы с коллекцией ролей."""

from typing import Any

from models.entity import Entity
from utils import same_name

DEFAULT_ROLE_NAMES = ("аналитик", "разработчик", "дизайнер", "тестировщик")


class Role(Entity):
    """Роль студента в проектной команде."""

    def __init__(self, role_id: int, name: str) -> None:
        """Создаёт роль."""
        super().__init__(role_id)
        self.name = name

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные роли для сохранения в JSON."""
        return {"id": self.id, "name": self.name}

    def __str__(self) -> str:
        """Возвращает название роли."""
        return self.name


def default_roles() -> list[Role]:
    """Создаёт стандартный набор ролей."""
    return [
        Role(role_id, name)
        for role_id, name in enumerate(DEFAULT_ROLE_NAMES, start=1)
    ]


def find_role(roles: list[Role], name: str) -> Role | None:
    """Ищет роль по названию без учёта регистра."""
    for role in roles:
        if same_name(role.name, name):
            return role
    return None


def find_role_by_id(roles: list[Role], role_id: int) -> Role | None:
    """Ищет роль по идентификатору."""
    for role in roles:
        if role.id == role_id:
            return role
    return None
