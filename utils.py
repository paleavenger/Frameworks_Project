"""Вспомогательные функции консольного интерфейса."""


def same_name(first: str, second: str) -> bool:
    """Сравнивает имена без учёта регистра и крайних пробелов."""
    return first.strip().casefold() == second.strip().casefold()


def input_int(prompt: str, minimum: int, maximum: int) -> int:
    """Запрашивает целое число в заданном диапазоне."""
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Введите число от {minimum} до {maximum}.")
        except ValueError:
            print("Ошибка: нужно ввести целое число.")


def input_non_empty(prompt: str) -> str:
    """Запрашивает непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Строка не может быть пустой.")
