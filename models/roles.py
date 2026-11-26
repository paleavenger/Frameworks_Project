from typing import Any

from models.entity import Entity
from utils import same_name

DEFAULT_ROLE_NAMES = ("аналитик", "разработчик", "дизайнер", "тестировщик")


# Role Представляет роль в команде
class Role(Entity):
    # __init__ Задаёт идентификатор и название
    def __init__(self, role_id: int, name: str) -> None:
        super().__init__(role_id)
        self.name = name

    # to_dict Возвращает данные роли для JSON
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

    # __str__ Возвращает название роли
    def __str__(self) -> str:
        return self.name


# default_roles Создаёт стандартный набор ролей
def default_roles() -> list[Role]:
    return [
        Role(role_id, name)
        for role_id, name in enumerate(DEFAULT_ROLE_NAMES, start=1)
    ]


# find_role Ищет роль по названию без учёта регистра
def find_role(roles: list[Role], name: str) -> Role | None:
    for role in roles:
        if same_name(role.name, name):
            return role
    return None


# find_role_by_id Ищет роль по идентификатору
def find_role_by_id(roles: list[Role], role_id: int) -> Role | None:
    for role in roles:
        if role.id == role_id:
            return role
    return None
