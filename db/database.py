import sqlite3
from pathlib import Path
from typing import Any, Sequence

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "teams.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


# get_connection Открывает базу SQLite
def get_connection(create: bool = False) -> sqlite3.Connection:
    if not create and not Path(DB_PATH).is_file():
        raise FileNotFoundError(
            f"База данных {DB_PATH} не найдена. "
            "Создайте её командой: python -m db.import_json"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# init_db Создаёт базу по схеме
def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection(create=True)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


# fetch_all Возвращает все строки запроса
def fetch_all(
    query: str,
    params: Sequence[Any] = (),
) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


# fetch_one Возвращает первую строку запроса
def fetch_one(
    query: str,
    params: Sequence[Any] = (),
) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()
