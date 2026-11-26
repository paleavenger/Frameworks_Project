from django.db import migrations, models


# Migration Создаёт таблицу студентов
class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.TextField(verbose_name='имя')),
                (
                    'specialty',
                    models.TextField(
                        blank=True,
                        default='',
                        verbose_name='специальность',
                    ),
                ),
            ],
        ),
    ]
