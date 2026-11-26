import django.db.models.deletion
from django.db import migrations, models


# Migration Создаёт таблицы команд, ролей и участников
class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
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
                (
                    'name',
                    models.TextField(
                        unique=True,
                        verbose_name='название',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
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
                (
                    'student',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='membership',
                        to='students.student',
                    ),
                ),
                (
                    'role',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='memberships',
                        to='teams.role',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Team',
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
                ('name', models.TextField(verbose_name='название')),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='teams',
                        to='projects.project',
                    ),
                ),
                (
                    'students',
                    models.ManyToManyField(
                        related_name='teams',
                        through='teams.Membership',
                        to='students.student',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='membership',
            name='team',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships',
                to='teams.team',
            ),
        ),
    ]
