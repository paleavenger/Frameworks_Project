import inspect
import re

import pytest
from django.contrib.staticfiles import finders
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext, override_settings
from django.urls import resolve, reverse

import homepage.views
import projects.views
import stats.views
import students.views
import teams.views
from db import import_json
from projects.models import Project
from students.models import Student
from teams.models import Membership, Team


@pytest.fixture
def client(orm_database) -> Client:
    return Client()


@pytest.mark.parametrize("url, view", [
    ("/", homepage.views.index),
    ("/students/", students.views.students),
    ("/students/1/", students.views.student_detail),
    ("/students/free/", students.views.free_students),
    ("/teams/", teams.views.teams),
    ("/teams/1/", teams.views.team_detail),
    ("/teams/vacancies/", teams.views.team_vacancies),
    ("/projects/", projects.views.projects),
    ("/projects/1/", projects.views.project_detail),
    ("/statistics/", stats.views.statistics),
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
    assert reverse("students:free") == "/students/free/"
    assert reverse("teams:vacancies") == "/teams/vacancies/"
    assert reverse("stats:index") == "/statistics/"


@pytest.mark.parametrize("url", [
    "/", "/students/", "/students/1/", "/students/free/", "/teams/",
    "/teams/1/", "/teams/vacancies/", "/projects/", "/projects/1/",
    "/statistics/",
])
def test_pages_return_valid_html(client, url: str) -> None:
    response = client.get(url)
    html = response.content.decode()
    assert response.status_code == 200
    assert html.startswith("<!DOCTYPE html>")
    assert "bootstrap" in html
    assert 'name="viewport"' in html
    for link in (
        "/", "/students/", "/teams/", "/projects/", "/statistics/",
    ):
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


def test_data_is_taken_from_django_database(client) -> None:
    assert "Иннокентий" not in client.get("/students/").content.decode()
    Student.objects.filter(pk=1).update(name="Иннокентий")
    assert "Иннокентий" in client.get("/students/").content.decode()


def test_json_changes_do_not_reach_pages_until_import(
    client, data_dir
) -> None:
    (data_dir / "students.json").write_text("[]", encoding="utf-8")
    assert "Анна" in client.get("/students/").content.decode()


def test_html_is_escaped(client) -> None:
    Student.objects.filter(pk=1).update(name="<script>alert(1)</script>")
    html = client.get("/students/").content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_unmigrated_database_returns_error_page(client, orm_database) -> None:
    connection.close()
    orm_database.unlink()
    response = client.get("/projects/")
    assert response.status_code == 500
    assert "python manage.py showmigrations" in response.content.decode()


def test_corrupted_database_returns_error_page(client, orm_database) -> None:
    connection.close()
    orm_database.write_bytes(b"not a database" * 100)
    response = client.get("/teams/")
    assert response.status_code == 500
    assert "Ошибка данных" in response.content.decode()


def template_names(response) -> list[str]:
    return [template.name for template in response.templates]


@pytest.mark.parametrize("url, template", [
    ("/", "homepage/index.html"),
    ("/students/", "students/student_list.html"),
    ("/students/1/", "students/student_detail.html"),
    ("/students/free/", "students/free_students.html"),
    ("/teams/", "teams/team_list.html"),
    ("/teams/1/", "teams/team_detail.html"),
    ("/teams/vacancies/", "teams/team_vacancies.html"),
    ("/projects/", "projects/project_list.html"),
    ("/projects/1/", "projects/project_detail.html"),
    ("/statistics/", "stats/statistics.html"),
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
    stats.views,
])
def test_views_contain_no_html(module) -> None:
    source = inspect.getsource(module)
    assert not re.search(r"</?[A-Za-z!]", source)
    assert "HttpResponse(" not in source
    assert "render(" in source


# test_sql_values_are_not_inserted_into_query_text Проверяет параметры SQL
@pytest.mark.parametrize("module", [
    homepage.views, students.views, teams.views, projects.views,
    stats.views, import_json,
])
def test_sql_values_are_not_inserted_into_query_text(module) -> None:
    source = inspect.getsource(module)
    assert not re.search(r'f"""|f"[^"]*\b(SELECT|INSERT|DELETE|UPDATE)\b',
                         source, re.IGNORECASE)
    assert ".format(" not in source
    assert "% (" not in source


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


def test_default_filter_for_missing_values(client) -> None:
    Membership.objects.all().delete()
    Student.objects.update(specialty="")
    html = client.get("/students/").content.decode()
    assert "специальность не указана" in html
    assert "без команды" in html


def test_length_filter_on_pages(client) -> None:
    assert "Всего студентов: 4" in client.get("/students/").content.decode()
    assert "Всего команд: 1" in client.get("/teams/").content.decode()
    assert "Всего проектов: 1" in client.get("/projects/").content.decode()


def test_empty_collections(client) -> None:
    Team.objects.all().delete()
    Student.objects.all().delete()
    Project.objects.all().delete()
    assert "Студенты не найдены." in client.get("/students/").content.decode()
    assert "Команды не найдены." in client.get("/teams/").content.decode()
    assert "Проекты не найдены." in client.get("/projects/").content.decode()


def test_team_without_members(client) -> None:
    Membership.objects.all().delete()
    html = client.get("/teams/1/").content.decode()
    assert "В команде пока нет участников." in html
    assert "0% — Команда пока пуста" in html


def test_ready_team_has_success_badge(client) -> None:
    Membership.objects.create(team_id=1, student_id=2, role_id=2)
    Membership.objects.create(team_id=1, student_id=3, role_id=4)
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


# page_text Извлекает текст веб-страницы
def page_text(client, url: str) -> str:
    html = client.get(url).content.decode()
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_free_students_page_lists_students_without_team(client) -> None:
    html = page_text(client, "/students/free/")
    assert "Найдено студентов: 3" in html
    assert "Глеб" in html and "Борис" in html and "Вера" in html
    assert "Анна" not in html


def test_free_students_filter_by_specialty(client) -> None:
    html = page_text(client, "/students/free/?specialty=разработка")
    assert "Найдено студентов: 2" in html
    assert "Глеб" in html and "Борис" in html
    assert "Вера" not in html
    raw = client.get("/students/free/?specialty=разработка").content.decode()
    assert re.search(r'value="разработка"\s+selected', raw)


def test_free_students_empty_result(client) -> None:
    html = page_text(client, "/students/free/?specialty=аналитика")
    assert "Найдено студентов: 0" in html
    assert "Свободных студентов по выбранным условиям нет." in html


def test_free_students_parameter_is_not_part_of_sql(client) -> None:
    response = client.get("/students/free/", {"specialty": "' OR 1=1 --"})
    assert response.status_code == 200
    assert "Найдено студентов: 0" in page_text(
        client, "/students/free/?specialty=%27+OR+1%3D1+--"
    )


def test_free_students_updates_after_joining_team(client) -> None:
    Membership.objects.create(team_id=1, student_id=4)
    html = page_text(client, "/students/free/")
    assert "Найдено студентов: 2" in html
    assert 'href="/students/4/"' not in html


def test_team_vacancies_default_and_filter(client) -> None:
    assert "Найдено команд, где свободно не менее 1 мест: 1" in page_text(
        client, "/teams/vacancies/"
    )
    html = page_text(client, "/teams/vacancies/?places=4")
    assert "свободно не менее 4 мест: 1" in html
    assert "свободных мест: 4" in html
    html = page_text(client, "/teams/vacancies/?places=5")
    assert "свободно не менее 5 мест: 0" in html
    assert "Команд с таким числом свободных мест нет." in html


@pytest.mark.parametrize("value, expected", [
    ("abc", 1), ("", 1), ("0", 1), ("-3", 1), ("99", 5), ("3", 3),
])
def test_team_vacancies_normalizes_places(
    client, value: str, expected: int
) -> None:
    response = client.get("/teams/vacancies/", {"places": value})
    assert response.status_code == 200
    assert response.context["places"] == expected


def test_team_vacancies_excludes_full_team(client) -> None:
    for number in (2, 3, 4):
        Membership.objects.create(team_id=1, student_id=number)
    student = Student.objects.create(name="?")
    Membership.objects.create(team_id=1, student=student)
    assert "свободно не менее 1 мест: 0" in page_text(
        client, "/teams/vacancies/"
    )


def test_statistics_page_values(client) -> None:
    html = page_text(client, "/statistics/")
    assert "Студентов: 4" in html
    assert "Команд: 1" in html
    assert "Проектов: 1" in html
    assert "Студентов без команды: 3" in html
    assert "Участников без роли: 0" in html
    assert "Средний размер команды: 1" in html
    assert "аналитик 1" in html
    assert "дизайнер 0" in html
    assert "Таких проектов пока нет." in html
    assert 'href="/teams/1/"' in client.get("/statistics/").content.decode()


def test_statistics_busy_projects_and_unready(client) -> None:
    Team.objects.create(name="Б", project_id=1)
    html = page_text(client, "/statistics/")
    assert "Журнал : команд 2" in html
    assert "Б : участников 0, с ролью 0" in html


def test_statistics_with_empty_database(client) -> None:
    Team.objects.all().delete()
    Student.objects.all().delete()
    Project.objects.all().delete()
    response = client.get("/statistics/")
    html = " ".join(response.content.decode().split())
    assert response.status_code == 200
    assert "Средний размер команды: нет данных" in html
    assert "Команд пока нет." in html
    assert "Все команды готовы к работе." in html


def test_list_pages_link_to_search_pages(client) -> None:
    students_html = client.get("/students/").content.decode()
    teams_html = client.get("/teams/").content.decode()
    assert 'href="/students/free/"' in students_html
    assert 'href="/teams/vacancies/"' in teams_html


def test_average_team_size_is_whole_number(client) -> None:
    team = Team.objects.create(name="Б", project_id=1)
    Membership.objects.create(team=team, student_id=2)
    Membership.objects.create(team=team, student_id=3)
    html = page_text(client, "/statistics/")
    assert "Средний размер команды: 2 " in html
    assert "1,5" not in html and "1.5" not in html


def test_student_search_supports_cyrillic_case(client) -> None:
    response = client.get("/students/", {"q": "  АНН  "})
    assert [student.name for student in response.context["students"]] == [
        "Анна",
    ]


def test_team_search_pagination_keeps_filters(client) -> None:
    for number in range(6):
        Team.objects.create(name=f"Команда {number}", project_id=1)
    other_project = Project.objects.create(title="Сайт")
    Team.objects.create(name="Журнал", project=other_project)
    filters = {"q": "ЖУРНАЛ", "project": 1, "sort": "readiness"}
    response = client.get("/teams/", filters)
    page = response.context["page_obj"]
    assert page.paginator.count == 7
    assert [team.name for team in page.object_list][:2] == [
        "Альфа", "Команда 0",
    ]
    assert "project=1&amp;sort=readiness&amp;page=2" in (
        response.content.decode()
    )
    response = client.get("/teams/", {**filters, "page": 2})
    assert [team.name for team in response.context["page_obj"]] == [
        "Команда 4", "Команда 5",
    ]


def test_team_list_accepts_invalid_parameters(client) -> None:
    response = client.get("/teams/", {
        "project": "не число", "sort": "invalid", "page": "invalid",
    })
    assert response.status_code == 200
    assert response.context["sort"] == "name"
    assert response.context["project_filter"] == ""
    assert response.context["page_obj"].number == 1


def test_readiness_filter_matches_statistics(client) -> None:
    empty = Team.objects.create(project_id=1, name="Пустая")
    ready = Team.objects.create(project_id=1, name="Готовая")
    for number in (2, 3, 4):
        Membership.objects.create(team=ready, student_id=number, role_id=1)

    for status, expected_id in (
        (Team.Status.EMPTY, empty.pk),
        (Team.Status.FORMING, 1),
        (Team.Status.READY, ready.pk),
    ):
        response = client.get("/teams/", {"status": status, "sort": "project"})
        assert [team.pk for team in response.context["page_obj"]] == [
            expected_id,
        ]

    response = client.get("/statistics/")
    assert response.context["team_status_counts"] == [
        (status.label, 1) for status in Team.Status
    ]


def test_projects_have_distinct_stable_public_addresses(client) -> None:
    first = Project.objects.create(title="Новый проект")
    second = Project.objects.create(title=first.title)
    original_url = first.get_absolute_url()
    assert original_url != second.get_absolute_url()
    first.title = "Новое название"
    first.save(update_fields=["title"])
    assert Project.objects.get(pk=first.pk).get_absolute_url() == original_url
    assert client.get(original_url).context["project"] == first
    missing = reverse("projects:by_slug", kwargs={"slug": "missing"})
    assert client.get(missing).status_code == 404


def test_query_counts_with_multiple_teams_and_members(client):
    for number in (2, 3, 4):
        Membership.objects.create(team_id=1, student_id=number)
        Team.objects.create(project_id=1, name=f"Команда {number}")
    expected_counts = {"/teams/": 3, "/teams/1/": 2, "/statistics/": 9}
    for url, expected in expected_counts.items():
        with CaptureQueriesContext(connection) as queries:
            assert client.get(url).status_code == 200
        assert len(queries) == expected, url
