"""Базовый класс сущностей предметной области."""

from typing import Any, Iterable


class Entity:
    """Сущность с идентификатором.

    Потомки определяют свои атрибуты, метод to_dict() для сохранения
    в JSON и строковое представление __str__().
    """

    def __init__(self, entity_id: int) -> None:
        """Создаёт сущность с указанным идентификатором."""
        self.id = entity_id

    def to_dict(self) -> dict[str, Any]:
        """Возвращает данные сущности для сохранения в JSON."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """Возвращает техническое представление для отладки."""
        return f"{type(self).__name__}(id={self.id})"


def next_id(entities: Iterable[Entity]) -> int:
    """Возвращает свободный идентификатор для новой сущности."""
    return max((entity.id for entity in entities), default=0) + 1
