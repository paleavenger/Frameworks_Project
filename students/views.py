"""Страницы со студентами."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.views import with_data
from models.students import find_student_by_id, sort_students
from models.teams import find_student_team
from storage import AppData


@with_data
def students(request: HttpRequest, data: AppData) -> HttpResponse:
    """Список студентов с командами, в которых они состоят."""
    entries = [
        (student, find_student_team(data.teams, student))
        for student in sort_students(data.students)
    ]
    return render(request, "students/student_list.html", {"entries": entries})


@with_data
def student_detail(
    request: HttpRequest,
    data: AppData,
    student_id: int,
) -> HttpResponse:
    """Карточка студента: специальность, команда и роль."""
    student = find_student_by_id(data.students, student_id)
    team = None
    role = None
    if student is not None:
        team = find_student_team(data.teams, student)
    if team is not None:
        role = team.find_member(student).role

    context = {"student": student, "team": team, "role": role}
    return render(
        request,
        "students/student_detail.html",
        context,
        status=404 if student is None else 200,
    )
