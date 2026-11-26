from django.db import migrations, models


# Migration Добавляет поле изображения проекта
class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_alter_project_options_project_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='image',
            field=models.ImageField(
                "изображение проекта", blank=True, upload_to="projects/",
                help_text=(
                    "PNG, JPEG или WebP. Максимальный размер файла — 5 МБ."
                ),
            ),
        ),
    ]
