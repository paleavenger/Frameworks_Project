import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection, transaction

from projects.models import Project
from students.models import Student
from teams.models import Membership, Role, Team

SOURCE_MODELS = (
    (Student, "students", "id, name, specialty"),
    (Project, "projects", "id, title"),
    (Role, "roles", "id, name"),
    (Team, "teams", "id, name, project_id"),
    (Membership, "team_members", "id, team_id, student_id, role_id"),
)


# read_source Читает снимок исходной базы
def read_source(path):
    uri = path.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as source:
        source.row_factory = sqlite3.Row
        source.execute("BEGIN")
        if source.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise CommandError("В базе ПР7 есть нарушенные внешние ключи.")
        return {
            table: source.execute(
                "SELECT " + columns + " FROM " + table + " ORDER BY id",
            ).fetchall()
            for _, table, columns in SOURCE_MODELS
        }


# Command Переносит данные ПР7 в Django
class Command(BaseCommand):
    help = "Переносит данные и связи из базы ПР7 в Django ORM."
    requires_migrations_checks = True

    # add_arguments Добавляет параметр пути к базе
    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=settings.BASE_DIR / "data" / "teams.sqlite",
            help="Путь к исходной базе SQLite из ПР7.",
        )

    # handle Импортирует записи с проверкой конфликтов
    def handle(self, *args, **options):
        path = options["source"].resolve()
        if not path.is_file():
            raise CommandError(f"База ПР7 не найдена: {path}")
        if path == Path(connection.settings_dict["NAME"]).resolve():
            raise CommandError("Исходная и целевая базы должны быть разными.")

        try:
            rows_by_table = read_source(path)
            with transaction.atomic():
                for model, table, _ in SOURCE_MODELS:
                    for row in rows_by_table[table]:
                        fields = dict(row)
                        pk = fields.pop("id")
                        obj, created = model.objects.get_or_create(
                            pk=pk, defaults=fields,
                        )
                        if not created and any(
                            getattr(obj, field) != value
                            for field, value in fields.items()
                        ):
                            raise CommandError(
                                f"Конфликт данных: {table}, ID {pk}. "
                                "Перенос отменён.",
                            )
        except (sqlite3.Error, DatabaseError) as error:
            raise CommandError(f"Ошибка переноса данных: {error}") from error

        counts = ", ".join(
            f"{table}: {len(rows)}" for table, rows in rows_by_table.items()
        )
        self.stdout.write(
            self.style.SUCCESS(f"Записи ПР7 в базе Django: {counts}"),
        )
