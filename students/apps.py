from django.apps import AppConfig


# StudentsConfig Настраивает приложение студентов
class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'students'
    verbose_name = "Студенты"
