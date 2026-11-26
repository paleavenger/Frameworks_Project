from typing import Any, Iterable


# Entity Хранит идентификатор сущности
class Entity:
    # __init__ Задаёт идентификатор
    def __init__(self, entity_id: int) -> None:
        self.id = entity_id

    # to_dict Определяет интерфейс сериализации
    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    # __repr__ Показывает тип и идентификатор
    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"


# next_id Возвращает следующий идентификатор
def next_id(entities: Iterable[Entity]) -> int:
    return max((entity.id for entity in entities), default=0) + 1
