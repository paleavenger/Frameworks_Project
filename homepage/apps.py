from django.apps import AppConfig
from django.db.backends.signals import connection_created


# register_casefold Добавляет функцию смены регистра в SQLite
def register_casefold(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_function(
            "unicode_casefold", 1, str.casefold, deterministic=True,
        )


# HomepageConfig Настраивает приложение главной страницы
class HomepageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "homepage"

    # ready Подключает обработчик соединений SQLite
    def ready(self):
        connection_created.connect(register_casefold)
