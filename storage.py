"""Работа с JSON-хранилищем проекта."""

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str, default: dict[str, Any]) -> dict[str, Any]:
    """Загружает JSON-файл или возвращает значение по умолчанию."""
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return default.copy()
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Не удалось прочитать {path}: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError(f"Файл {path} должен содержать JSON-объект")
    return data


def save_json(filename: str, data: dict[str, Any]) -> None:
    """Сохраняет данные в JSON-файл."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError as error:
        raise RuntimeError(f"Не удалось записать {path}: {error}") from error
