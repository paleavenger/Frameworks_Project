from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# Project Хранит название, адрес и изображение проекта
class Project(models.Model):
    title = models.TextField("название")
    slug = models.SlugField(
        "адрес", max_length=180, allow_unicode=True, unique=True, blank=True,
        help_text="Создаётся из названия и сохраняется при переименовании.",
    )
    image = models.ImageField(
        "изображение проекта", upload_to="projects/", blank=True,
        help_text="PNG, JPEG или WebP. Максимальный размер файла — 5 МБ.",
    )

    # Meta Задаёт подписи модели проекта
    class Meta:
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    # save Создаёт адрес при первом сохранении
    def save(self, *args, **kwargs):
        if not self.slug:
            title_slug = slugify(self.title, allow_unicode=True)[:140]
            self.slug = f"{title_slug or 'project'}-{uuid4().hex}"
        super().save(*args, **kwargs)

    # get_absolute_url Возвращает адрес проекта
    def get_absolute_url(self):
        return reverse("projects:by_slug", kwargs={"slug": self.slug})

    # __str__ Возвращает название проекта
    def __str__(self) -> str:
        return self.title
