"""Страницы с командами."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.views import with_data
from models.teams import find_team_by_id, sort_teams
from storage import AppData


@with_data
def teams(request: HttpRequest, data: AppData) -> HttpResponse:
    """Список команд с проектом, составом и готовностью."""
    context = {"teams": sort_teams(data.teams)}
    return render(request, "teams/team_list.html", context)


@with_data
def team_detail(
    request: HttpRequest,
    data: AppData,
    team_id: int,
) -> HttpResponse:
    """Карточка команды: проект, готовность и состав с ролями."""
    team = find_team_by_id(data.teams, team_id)
    return render(
        request,
        "teams/team_detail.html",
        {"team": team},
        status=404 if team is None else 200,
    )
