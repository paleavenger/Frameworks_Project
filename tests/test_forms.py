from io import BytesIO
from types import ModuleType

import pytest
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from PIL import Image

from projects.models import Project
from students.models import Student
from teams.models import Membership, Team


@pytest.fixture
def editor(orm_database):
    user = get_user_model().objects.create_superuser(username="form_editor")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    return client


def submit(client, url, data, *, token_page=None, follow=False):
    client.get(token_page or url)
    token = client.cookies["csrftoken"].value
    payload = {**data, "csrfmiddlewaretoken": token}
    return client.post(url, payload, follow=follow)


def test_team_filter_displays_errors_and_applies_valid_fields(orm_database):
    Team.objects.create(project_id=1, name="Другая")
    response = Client().get("/teams/", {
        "q": "АЛЬФА", "sort": "bad-sort", "project": "bad-id",
    })
    form = response.context["form"]
    assert set(form.errors) == {"project", "sort"}
    assert [team.name for team in response.context["page_obj"]] == ["Альфа"]
    assert "Выберите проект из списка." in response.content.decode()


def test_membership_create_edit_and_remove(editor):
    create = reverse("teams:membership_create", args=[1])
    other = Team.objects.create(project_id=1, name="Другая")
    assert editor.get(create).status_code == 200
    response = submit(editor, create, {
        "student": 2, "team": other.pk, "role": 1,
    })
    member = Membership.objects.get(student_id=2)
    assert response.url == "/teams/1/"
    assert member.team_id == 1

    update = reverse("teams:membership_update", args=[1, member.pk])
    form = editor.get(update).context["form"]
    assert form.initial["role"] == 1
    assert submit(editor, update, {"team": 1, "role": 2}).url == "/teams/1/"
    response = submit(editor, update, {
        "student": 3, "team": other.pk, "role": 2,
    })
    member.refresh_from_db()
    assert (member.student_id, member.team_id, member.role_id) == (
        2, other.pk, 2,
    )
    assert response.url == other.get_absolute_url()
    assert editor.get(update).status_code == 404

    remove = reverse("teams:membership_remove", args=[other.pk, member.pk])
    assert editor.get(remove).status_code == 405
    assert editor.post(remove).status_code == 403
    assert not Team.objects.with_vacancies(5).filter(pk=other.pk).exists()
    response = submit(editor, remove, {}, token_page=other.get_absolute_url())
    assert response.url == other.get_absolute_url()
    assert Team.objects.with_vacancies(5).filter(pk=other.pk).exists()
    assert Student.objects.filter(pk=2, membership__isnull=True).exists()


def test_membership_forms_validate_duplicate_and_full_team(editor):
    create = reverse("teams:membership_create", args=[1])
    response = submit(editor, create, {"student": 1})
    assert "Студент уже состоит в команде." in (
        response.context["form"].errors["student"]
    )
    for number in (2, 3, 4):
        Membership.objects.create(team_id=1, student_id=number)
    fifth = Student.objects.create(name="Пятый")
    Membership.objects.create(team_id=1, student=fifth)
    sixth = Student.objects.create(name="Шестой")
    response = submit(editor, create, {"student": sixth.pk})
    assert "В команде не более 5 участников" in (
        response.context["form"].errors["team"]
    )
    assert not Membership.objects.filter(student=sixth).exists()

    other = Team.objects.create(project_id=1, name="Другая")
    member = Membership.objects.create(team=other, student=sixth)
    update = reverse("teams:membership_update", args=[other.pk, member.pk])
    response = submit(editor, update, {"team": 1})
    assert "team" in response.context["form"].errors
    member.refresh_from_db()
    assert member.team == other


def test_forms_require_permission_and_csrf(editor):
    add = reverse("teams:membership_create", args=[1])
    image = reverse("projects:image", args=[1])
    assert editor.post(add, {"student": 2}).status_code == 403
    assert editor.post(image).status_code == 403
    assert Client().get(add).url.startswith("/admin/login/?next=")
    missing = reverse("teams:membership_create", args=[999])
    assert editor.get(missing).status_code == 404
    unprivileged = get_user_model().objects.create_user(username="reader")
    client = Client()
    client.force_login(unprivileged)
    assert client.get(add).status_code == 403
    assert client.get(image).status_code == 403


def image_upload(name="photo.png", color="red", image_format="PNG"):
    buffer = BytesIO()
    Image.new("RGB", (20, 12), color).save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue())


def test_project_image_upload_display_and_admin_replacement(editor, tmp_path):
    project = Project.objects.get(pk=1)
    address = reverse("projects:image", args=[project.pk])
    media_root = tmp_path / "media"
    with override_settings(MEDIA_ROOT=media_root):
        assert b"multipart/form-data" in editor.get(address).content
        response = submit(editor, address, {"image": image_upload()})
        assert response.url == project.get_absolute_url()
        project.refresh_from_db()
        original = project.image.name
        assert original.startswith("projects/")
        assert (media_root / original).is_file()
        response = editor.get(project.get_absolute_url())
        assert project.image.url in response.content.decode()
        media_urls = ModuleType("test_media_urls")
        media_urls.urlpatterns = static(
            settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
        )
        with override_settings(ROOT_URLCONF=media_urls):
            media = editor.get(project.image.url)
            assert media.status_code == 200
            media.close()

        admin_url = reverse("admin:projects_project_change", args=[project.pk])
        response = submit(editor, admin_url, {
            "title": project.title,
            "image": image_upload(color="blue"),
            "teams-TOTAL_FORMS": 1,
            "teams-INITIAL_FORMS": 1,
            "teams-MIN_NUM_FORMS": 0,
            "teams-MAX_NUM_FORMS": 0,
            "teams-0-id": 1,
            "teams-0-project": project.pk,
        })
        assert response.status_code == 302
        project.refresh_from_db()
        assert original != project.image.name
        assert project.image.url in (
            editor.get(project.get_absolute_url()).content.decode()
        )


@pytest.mark.parametrize("upload", (
    lambda: SimpleUploadedFile("broken.png", b"not an image"),
    lambda: image_upload("image.gif", image_format="GIF"),
))
def test_invalid_images_are_not_saved(editor, tmp_path, upload):
    media_root = tmp_path / "media"
    with override_settings(MEDIA_ROOT=media_root):
        response = submit(editor, reverse("projects:image", args=[1]), {
            "image": upload(),
        })
        assert "image" in response.context["form"].errors
        assert not Project.objects.get(pk=1).image
        assert not media_root.exists()
