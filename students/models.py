from django.db import models


class Student(models.Model):
    name = models.TextField("имя")
    specialty = models.TextField("специальность", blank=True, default="")

    class Meta:
        verbose_name = "студент"
        verbose_name_plural = "студенты"

    def __str__(self) -> str:
        return self.name
