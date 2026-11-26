from django.apps import AppConfig


# StatsConfig Настраивает приложение статистики
class StatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats'
