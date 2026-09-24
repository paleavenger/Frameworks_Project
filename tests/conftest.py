"""Настройка пути для импорта модулей проекта в тестах."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))
