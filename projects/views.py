from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from homepage.views import with_db
from projects.models import Project
from teams.models import Team

from .forms import ProjectImageForm


# projects Показывает проекты и число команд
@with_db
def projects(request: HttpRequest) -> HttpResponse:
    projects_data = Project.objects.annotate(
        teams_count=Count("teams"),
    ).order_by("title")
    return render(
        request,
        "projects/project_list.html",
        {"projects": projects_data},
    )


# project_detail Показывает карточку проекта и его команды
@with_db
def project_detail(
    request: HttpRequest,
    project_id: int | None = None,
    slug: str | None = None,
) -> HttpResponse:
    lookup = {"slug": slug} if slug is not None else {"pk": project_id}
    try:
        project = Project.objects.get(**lookup)
    except Project.DoesNotExist:
        project = None
    teams = (
        project.teams.order_by("name") if project is not None
        else Team.objects.none()
    )
    return render(
        request,
        "projects/project_detail.html",
        {"project": project, "teams": teams},
        status=404 if project is None else 200,
    )


# project_image Обновляет изображение проекта
@require_http_methods(["GET", "HEAD", "POST"])
@login_required(login_url=reverse_lazy("admin:login"))
@permission_required("projects.change_project", raise_exception=True)
@with_db
def project_image(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    data = request.POST if request.method == "POST" else None
    form = ProjectImageForm(data, request.FILES, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save(commit=False).save(update_fields=["image"])
        messages.success(request, "Изображение проекта обновлено.")
        return redirect(project)
    return render(request, "projects/project_image.html", {
        "form": form, "project": project,
    })
