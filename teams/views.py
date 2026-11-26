from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST

from homepage.lookups import Casefold
from homepage.views import with_db
from projects.models import Project
from teams.models import Membership, Team

from .forms import MembershipForm, TeamFilterForm

TEAMS_PER_PAGE = 5
ADMIN_LOGIN = reverse_lazy("admin:login")


# teams Показывает команды и применяет корректные фильтры
@with_db
def teams(request: HttpRequest) -> HttpResponse:
    projects = Project.objects.order_by("title", "pk").values_list(
        "pk", "title",
    )
    form = TeamFilterForm(request.GET, projects=projects)
    form.is_valid()
    query = form.cleaned_data.get("q", "")
    project = form.cleaned_data.get("project")
    sort = form.cleaned_data.get("sort") or "name"
    status = form.cleaned_data.get("status", "")

    teams_data = Team.objects.with_readiness().select_related("project")
    if query:
        search = query.casefold()
        teams_data = teams_data.alias(
            search_name=Casefold("name"),
            search_project=Casefold("project__title"),
        ).filter(
            Q(search_name__contains=search)
            | Q(search_project__contains=search),
        )
    if project:
        teams_data = teams_data.filter(project__pk=project)
    if status:
        teams_data = teams_data.filter(readiness_status=status)
    teams_data = teams_data.order_by(*TeamFilterForm.ORDERING[sort])
    paginator = Paginator(teams_data, TEAMS_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        "teams": page,
        "page_obj": page,
        "form": form,
        "project_filter": str(project) if project is not None else "",
        "sort": sort,
        "status": status,
        "max_size": Team.MAX_SIZE,
    }
    return render(request, "teams/team_list.html", context)


# team_detail Показывает состав и готовность команды
@with_db
def team_detail(request: HttpRequest, team_id: int) -> HttpResponse:
    try:
        team = Team.objects.with_readiness().select_related("project").get(
            pk=team_id,
        )
    except Team.DoesNotExist:
        team = None
    members = Membership.objects.none()
    if team is not None:
        members = team.memberships.select_related(
            "student", "role",
        ).order_by("student__name")
    context = {"team": team, "members": members, "max_size": Team.MAX_SIZE}
    return render(
        request,
        "teams/team_detail.html",
        context,
        status=404 if team is None else 200,
    )


# parse_places Приводит число мест к допустимому диапазону
def parse_places(value: str) -> int:
    try:
        places = int(value)
    except ValueError:
        places = 1
    return min(max(places, 1), Team.MAX_SIZE)


# team_vacancies Показывает команды со свободными местами
@with_db
def team_vacancies(request: HttpRequest) -> HttpResponse:
    places = parse_places(request.GET.get("places", "1"))
    teams_data = Team.objects.with_vacancies(places).select_related(
        "project",
    ).order_by("-free_places", "name")
    context = {
        "teams": teams_data,
        "places": places,
        "places_choices": range(1, Team.MAX_SIZE + 1),
        "max_size": Team.MAX_SIZE,
    }
    return render(request, "teams/team_vacancies.html", context)


# edit_membership Обрабатывает форму участия в команде
def edit_membership(request, team, membership=None):
    data = request.POST if request.method == "POST" else None
    form = MembershipForm(data, instance=membership, initial={"team": team.pk})
    if membership is None:
        form.fields["team"].disabled = True
    if request.method == "POST" and form.is_valid():
        try:
            if membership is None:
                member = form.save()
            else:
                member = form.save(commit=False)
                member.save(update_fields=("team", "role"))
        except IntegrityError:
            form.add_error(
                None, "Состав команды изменился. Проверьте студента и места.",
            )
        else:
            messages.success(request, "Состав команды сохранён.")
            return redirect(member.team)
    return render(request, "teams/membership_form.html", {
        "form": form, "team": team, "membership": membership,
    })


# membership_create Добавляет студента в команду
@require_http_methods(["GET", "HEAD", "POST"])
@login_required(login_url=ADMIN_LOGIN)
@permission_required("teams.add_membership", raise_exception=True)
@with_db
def membership_create(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    return edit_membership(request, team)


# membership_update Изменяет участие студента в команде
@require_http_methods(["GET", "HEAD", "POST"])
@login_required(login_url=ADMIN_LOGIN)
@permission_required("teams.change_membership", raise_exception=True)
@with_db
def membership_update(request, team_id, membership_id):
    membership = get_object_or_404(
        Membership.objects.select_related("team", "student"),
        pk=membership_id, team_id=team_id,
    )
    return edit_membership(request, membership.team, membership)


# membership_remove Удаляет студента из команды
@require_POST
@login_required(login_url=ADMIN_LOGIN)
@permission_required("teams.delete_membership", raise_exception=True)
@with_db
def membership_remove(request, team_id, membership_id):
    membership = get_object_or_404(
        Membership, pk=membership_id, team_id=team_id,
    )
    membership.delete()
    messages.success(request, "Участник удалён из команды.")
    return redirect("teams:detail", team_id=team_id)
