import django.db.models.deletion
from django.db import migrations, models


# Migration Обновляет подписи и связи моделей команд
class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_alter_project_options_project_slug'),
        ('students', '0002_alter_student_options'),
        ('teams', '0002_membership_capacity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='membership',
            options={
                "verbose_name": "участие в команде",
                "verbose_name_plural": "состав команд",
            },
        ),
        migrations.AlterModelOptions(
            name='role',
            options={'verbose_name': 'роль', 'verbose_name_plural': 'роли'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={
                "verbose_name": "команда",
                "verbose_name_plural": "команды",
            },
        ),
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="memberships", to="teams.role",
                verbose_name="роль",
                help_text="Оставьте поле пустым, если роль ещё не назначена.",
            ),
        ),
        migrations.AlterField(
            model_name='membership',
            name='student',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="membership", to="students.student",
                verbose_name="студент",
            ),
        ),
        migrations.AlterField(
            model_name='membership',
            name='team',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="memberships", to="teams.team",
                verbose_name="команда",
            ),
        ),
        migrations.AlterField(
            model_name='team',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="teams", to="projects.project",
                verbose_name="проект",
            ),
        ),
        migrations.AlterField(
            model_name='team',
            name='students',
            field=models.ManyToManyField(
                related_name="teams", through="teams.Membership",
                to="students.student", verbose_name="студенты",
            ),
        ),
    ]
