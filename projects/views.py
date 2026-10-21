"""Страницы с проектами."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.views import with_data
from models.projects import find_project_by_id
from storage import AppData


@with_data
def projects(request: HttpRequest, data: AppData) -> HttpResponse:
    """Список проектов и число работающих над ними команд."""
    entries = [
        (
            project,
            sum(team.project is project for team in data.teams),
        )
        for project in sorted(data.projects, key=lambda p: p.title.lower())
    ]
    return render(request, "projects/project_list.html", {"entries": entries})


@with_data
def project_detail(
    request: HttpRequest,
    data: AppData,
    project_id: int,
) -> HttpResponse:
    """Карточка проекта со списком команд, которые над ним работают."""
    project = find_project_by_id(data.projects, project_id)
    teams = [team for team in data.teams if team.project is project]
    context = {"project": project, "teams": teams}
    return render(
        request,
        "projects/project_detail.html",
        context,
        status=404 if project is None else 200,
    )
