from django.db import migrations, models
from django.utils.text import slugify


# fill_project_slugs Заполняет адреса существующих проектов
def fill_project_slugs(apps, schema_editor):
    project_model = apps.get_model("projects", "Project")
    projects = project_model.objects.using(schema_editor.connection.alias)
    for project in projects.only("pk", "title").iterator():
        title_slug = slugify(project.title, allow_unicode=True)[:140]
        projects.filter(pk=project.pk).update(
            slug=f"{title_slug or 'project'}-{project.pk}",
        )


# Migration Добавляет адреса проектов
class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={
                "verbose_name": "проект",
                "verbose_name_plural": "проекты",
            },
        ),
        migrations.AddField(
            model_name='project',
            name='slug',
            field=models.SlugField(max_length=180, null=True),
        ),
        migrations.RunPython(fill_project_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=models.SlugField(
                "адрес", allow_unicode=True, blank=True, max_length=180,
                unique=True,
                help_text=(
                    "Создаётся из названия и сохраняется при переименовании."
                ),
            ),
        ),
    ]
