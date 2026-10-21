"""Тесты веб-интерфейса: маршруты, view-функции и страницы."""

import inspect

import pytest
from django.contrib.staticfiles import finders
from django.test import Client
from django.test.utils import override_settings
from django.urls import resolve, reverse

import homepage.views
import storage
import projects.views
import students.views
import teams.views
from models.projects import Project
from models.roles import default_roles
from models.students import Student
from models.teams import Team


@pytest.fixture
def client(data_dir) -> Client:
    return Client()


@pytest.mark.parametrize("url, view", [
    ("/", homepage.views.index),
    ("/students/", students.views.students),
    ("/students/1/", students.views.student_detail),
    ("/teams/", teams.views.teams),
    ("/teams/1/", teams.views.team_detail),
    ("/projects/", projects.views.projects),
    ("/projects/1/", projects.views.project_detail),
])
def test_url_resolves_to_view(url: str, view) -> None:
    assert resolve(url).func.__wrapped__ is view.__wrapped__


def test_dynamic_url_passes_id() -> None:
    assert resolve("/students/7/").kwargs == {"student_id": 7}
    assert resolve("/teams/7/").kwargs == {"team_id": 7}
    assert resolve("/projects/7/").kwargs == {"project_id": 7}


def test_reverse_by_route_names() -> None:
    assert reverse("homepage:index") == "/"
    assert reverse("students:list") == "/students/"
    assert reverse("students:detail", args=[1]) == "/students/1/"
    assert reverse("teams:list") == "/teams/"
    assert reverse("teams:detail", args=[3]) == "/teams/3/"
    assert reverse("projects:list") == "/projects/"
    assert reverse("projects:detail", args=[2]) == "/projects/2/"


@pytest.mark.parametrize("url", [
    "/", "/students/", "/students/1/", "/teams/", "/teams/1/",
    "/projects/", "/projects/1/",
])
def test_pages_return_valid_html(client, url: str) -> None:
    response = client.get(url)
    html = response.content.decode()
    assert response.status_code == 200
    assert html.startswith("<!DOCTYPE html>")
    assert "bootstrap" in html
    assert 'name="viewport"' in html
    for link in ("/", "/students/", "/teams/", "/projects/"):
        assert f'href="{link}"' in html


def test_home_page(client) -> None:
    html = " ".join(client.get("/").content.decode().split())
    assert "Система управления учебными проектными командами" in html
    assert "Студентов: 4, команд: 1, проектов: 1." in html


def test_students_list(client) -> None:
    html = client.get("/students/").content.decode()
    assert 'href="/students/1/"' in html
    assert "Глеб" in html
    assert "без команды" in html
    assert 'href="/teams/1/"' in html


def test_student_detail(client) -> None:
    html = client.get("/students/1/").content.decode()
    assert "Анна" in html
    assert "аналитика" in html
    assert "Альфа" in html
    assert "аналитик" in html


def test_student_without_team(client) -> None:
    html = client.get("/students/4/").content.decode()
    assert "Глеб" in html
    assert "без команды" in html


def test_teams_list(client) -> None:
    html = client.get("/teams/").content.decode()
    assert 'href="/teams/1/"' in html
    assert "Журнал" in html
    assert "1 из 5" in html
    assert "Нужно не менее 3 участников" in html


def test_team_detail(client) -> None:
    html = client.get("/teams/1/").content.decode()
    assert "Альфа" in html
    assert 'href="/projects/1/"' in html
    assert 'href="/students/1/"' in html
    assert "роль: аналитик" in html
    assert "1 из 5" in html


def test_projects_pages(client) -> None:
    listing = client.get("/projects/").content.decode()
    detail = client.get("/projects/1/").content.decode()
    assert "Команд: 1" in listing
    assert 'href="/teams/1/"' in detail


@pytest.mark.parametrize("url, text", [
    ("/students/999/", "Студент не найден"),
    ("/teams/999/", "Команда не найдена"),
    ("/projects/999/", "Проект не найден"),
])
def test_missing_object_returns_404(client, url: str, text: str) -> None:
    response = client.get(url)
    assert response.status_code == 404
    assert text in response.content.decode()


def test_non_numeric_id_is_not_routed(client) -> None:
    assert client.get("/students/abc/").status_code == 404


@override_settings(DEBUG=False)
def test_custom_404_page(client) -> None:
    response = client.get("/nonexistent/")
    html = response.content.decode()
    assert response.status_code == 404
    assert "404 — страница не найдена" in html
    assert 'href="/"' in html


def test_data_is_taken_from_json(client, data_dir) -> None:
    students = storage.load_students()
    students[0] = Student(1, "Иннокентий", "аналитика")
    storage.save_entities("students.json", students)
    assert "Иннокентий" in client.get("/students/").content.decode()


def test_html_is_escaped(client, data_dir) -> None:
    storage.save_entities(
        "students.json", [Student(1, "<script>alert(1)</script>", "x")]
    )
    storage.save_entities("teams.json", [])
    html = client.get("/students/").content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_broken_data_returns_error_page(client, data_dir) -> None:
    (data_dir / "students.json").write_text("{", encoding="utf-8")
    response = client.get("/students/")
    assert response.status_code == 500
    assert "Ошибка данных" in response.content.decode()


def template_names(response) -> list[str]:
    return [template.name for template in response.templates]


@pytest.mark.parametrize("url, template", [
    ("/", "homepage/index.html"),
    ("/students/", "students/student_list.html"),
    ("/students/1/", "students/student_detail.html"),
    ("/teams/", "teams/team_list.html"),
    ("/teams/1/", "teams/team_detail.html"),
    ("/projects/", "projects/project_list.html"),
    ("/projects/1/", "projects/project_detail.html"),
])
def test_page_uses_template_that_extends_base(
    client, url: str, template: str
) -> None:
    names = template_names(client.get(url))
    assert template in names
    assert "base.html" in names
    assert "includes/navigation.html" in names


@pytest.mark.parametrize("url, include", [
    ("/students/", "students/includes/student_card.html"),
    ("/students/", "students/includes/team_badge.html"),
    ("/students/1/", "students/includes/team_badge.html"),
    ("/teams/", "teams/includes/team_card.html"),
    ("/teams/", "teams/includes/readiness_badge.html"),
    ("/teams/1/", "teams/includes/readiness_badge.html"),
    ("/projects/", "projects/includes/project_card.html"),
])
def test_page_uses_include(client, url: str, include: str) -> None:
    assert include in template_names(client.get(url))


def test_list_page_repeats_card_for_each_object(client) -> None:
    names = template_names(client.get("/students/"))
    assert names.count("students/includes/student_card.html") == 4


def test_views_do_not_use_page_function() -> None:
    assert not hasattr(homepage.views, "page")
    assert not hasattr(homepage.views, "not_found")


@pytest.mark.parametrize("module", [
    homepage.views, students.views, teams.views, projects.views,
])
def test_views_contain_no_html(module) -> None:
    source = inspect.getsource(module)
    assert "<" not in source.replace("->", "").replace("<int", "")
    assert "HttpResponse(" not in source
    assert "render(" in source


def test_navigation_is_built_with_url_names(client) -> None:
    html = client.get("/teams/").content.decode()
    assert 'href="/students/"' in html
    assert 'class="nav-link active"' in html
    assert html.count("nav-link active") == 1


def test_static_files_are_connected(client) -> None:
    html = client.get("/").content.decode()
    assert "/static/homepage/css/style.css" in html
    assert "/static/homepage/js/main.js" in html
    assert "/static/homepage/img/logo.png" in html
    assert 'id="current-year"' in html
    for path in (
        "homepage/css/style.css",
        "homepage/js/main.js",
        "homepage/img/logo.png",
    ):
        assert finders.find(path), path


def test_default_filter_for_missing_values(client, data_dir) -> None:
    storage.save_entities("students.json", [Student(1, "Анна", "")])
    storage.save_entities("teams.json", [])
    html = client.get("/students/").content.decode()
    assert "специальность не указана" in html
    assert "без команды" in html


def test_length_filter_on_pages(client) -> None:
    assert "Всего студентов: 4" in client.get("/students/").content.decode()
    assert "Всего команд: 1" in client.get("/teams/").content.decode()
    assert "Всего проектов: 1" in client.get("/projects/").content.decode()


def test_empty_collections(client, data_dir) -> None:
    for name in ("students", "projects", "teams"):
        storage.save_entities(f"{name}.json", [])
    assert "Студенты не найдены." in client.get("/students/").content.decode()
    assert "Команды не найдены." in client.get("/teams/").content.decode()
    assert "Проекты не найдены." in client.get("/projects/").content.decode()


def test_team_without_members(client, data_dir) -> None:
    empty_team = Team(1, "Пустая", Project(1, "Журнал"))
    storage.save_entities("teams.json", [empty_team])
    html = client.get("/teams/1/").content.decode()
    assert "В команде пока нет участников." in html
    assert "0% — Команда пока пуста" in html


def test_ready_team_has_success_badge(client, data_dir) -> None:
    roles = default_roles()
    team = Team(1, "Альфа", Project(1, "Журнал"))
    for number, role in enumerate(roles[:3], start=1):
        team.add_member(Student(number, f"С{number}", "x"), role)
    storage.save_entities("students.json", [m.student for m in team.members])
    storage.save_entities("teams.json", [team])
    html = client.get("/teams/1/").content.decode()
    assert "bg-success" in html
    assert "100% — Команда готова к работе" in html


def test_404_templates_have_status_and_message(client) -> None:
    for url, text in (
        ("/students/999/", "Студент не найден"),
        ("/teams/999/", "Команда не найдена"),
        ("/projects/999/", "Проект не найден"),
    ):
        response = client.get(url)
        assert response.status_code == 404
        assert text in template_text(response)
        assert "base.html" in template_names(response)


def template_text(response) -> str:
    return response.content.decode()


@override_settings(DEBUG=False)
def test_404_handler_uses_template(client) -> None:
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "404.html" in template_names(response)
