from django.db.models import Avg, Count, Q
from django.db.models.functions import Round
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.views import with_db
from projects.models import Project
from students.models import Student
from teams.models import Membership, Role, Team

TOP_TEAMS_LIMIT = 3
BUSY_PROJECT_TEAMS = 1


# statistics Показывает сводную статистику
@with_db
def statistics(request: HttpRequest) -> HttpResponse:
    teams_with_status = Team.objects.with_readiness_status()
    team_counts = teams_with_status.aggregate(
        teams_count=Count("pk"),
        avg_team_size=Round(Avg("members_count")),
        empty=Count("pk", filter=Q(readiness_status=Team.Status.EMPTY)),
        forming=Count("pk", filter=Q(readiness_status=Team.Status.FORMING)),
        ready=Count("pk", filter=Q(readiness_status=Team.Status.READY)),
    )
    average = team_counts["avg_team_size"]
    student_counts = Student.objects.aggregate(
        students_count=Count("pk"),
        free_students_count=Count("pk", filter=Q(membership__isnull=True)),
    )
    totals = {
        **student_counts,
        "teams_count": team_counts["teams_count"],
        "projects_count": Project.objects.count(),
        "without_role_count": Membership.objects.filter(
            role__isnull=True,
        ).count(),
        "avg_team_size": int(average) if average is not None else None,
    }
    by_specialty = Student.objects.values("specialty").annotate(
        students_count=Count("pk"),
    ).order_by("-students_count", "specialty")
    by_role = Role.objects.annotate(
        members_count=Count("memberships"),
    ).order_by("-members_count", "name")
    top_teams = Team.objects.with_readiness().order_by(
        "-readiness_percent", "name",
    )[:TOP_TEAMS_LIMIT]
    busy_projects = Project.objects.annotate(
        teams_count=Count("teams"),
    ).filter(
        teams_count__gt=BUSY_PROJECT_TEAMS,
    ).order_by("-teams_count", "title")
    unready_teams = teams_with_status.exclude(
        readiness_status=Team.Status.READY,
    ).order_by("name")
    context = {
        "totals": totals,
        "team_status_counts": [
            (status.label, team_counts[status.value]) for status in Team.Status
        ],
        "by_specialty": by_specialty,
        "by_role": by_role,
        "top_teams": top_teams,
        "top_teams_limit": TOP_TEAMS_LIMIT,
        "busy_projects": busy_projects,
        "busy_project_teams": BUSY_PROJECT_TEAMS,
        "unready_teams": unready_teams,
        "min_size": Team.MIN_SIZE,
    }
    return render(request, "stats/statistics.html", context)
