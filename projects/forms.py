from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Project


# ProjectImageForm Принимает изображение проекта
class ProjectImageForm(forms.ModelForm):
    # Meta Настраивает поле загрузки
    class Meta:
        model = Project
        fields = ("image",)
        widgets = {
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/png,image/jpeg,image/webp",
            }),
        }

    # clean_image Проверяет размер и формат изображения
    def clean_image(self):
        image = self.cleaned_data["image"]
        if not isinstance(image, UploadedFile):
            return image

        if image.size > 5 * 1024 ** 2:
            raise ValidationError("Выберите изображение размером до 5 МБ.")
        extensions = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}
        extension = extensions.get(image.image.format)
        if not extension:
            raise ValidationError("Загрузите изображение PNG, JPEG или WebP.")
        image.name = f"{uuid4().hex}.{extension}"
        return image
