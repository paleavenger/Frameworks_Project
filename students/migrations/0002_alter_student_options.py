from django.db import migrations


# Migration Обновляет подписи модели студента
class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='student',
            options={
                "verbose_name": "студент",
                "verbose_name_plural": "студенты",
            },
        ),
    ]
