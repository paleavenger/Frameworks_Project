# same_name Сравнивает имена без учёта регистра и пробелов
def same_name(first: str, second: str) -> bool:
    return first.strip().casefold() == second.strip().casefold()


# input_int Запрашивает целое число в диапазоне
def input_int(prompt: str, minimum: int, maximum: int) -> int:
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Введите число от {minimum} до {maximum}.")
        except ValueError:
            print("Ошибка: нужно ввести целое число.")


# input_non_empty Запрашивает непустую строку
def input_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Строка не может быть пустой.")
