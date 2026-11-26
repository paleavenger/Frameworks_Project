from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.lookups import Casefold
from homepage.views import with_db
from students.models import Student


# students Показывает список студентов с поиском
@with_db
def students(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    students_data = Student.objects.select_related(
        "membership__team",
    ).order_by("name", "pk")
    if query:
        students_data = students_data.alias(
            search_name=Casefold("name"),
        ).filter(search_name__contains=query.casefold())
    return render(
        request,
        "students/student_list.html",
        {"students": students_data, "query": query},
    )


# student_detail Показывает студента, его команду и роль
@with_db
def student_detail(request: HttpRequest, student_id: int) -> HttpResponse:
    try:
        student = Student.objects.select_related(
            "membership__team", "membership__role",
        ).get(pk=student_id)
    except Student.DoesNotExist:
        student = None
    return render(
        request,
        "students/student_detail.html",
        {"student": student},
        status=404 if student is None else 200,
    )


# free_students Показывает студентов без команды
@with_db
def free_students(request: HttpRequest) -> HttpResponse:
    specialty = request.GET.get("specialty", "").strip()
    specialties = Student.objects.exclude(specialty="").values(
        "specialty",
    ).order_by("specialty").distinct()
    students_data = Student.objects.filter(
        membership__isnull=True,
    ).order_by("name")
    if specialty:
        students_data = students_data.filter(specialty=specialty)
    context = {
        "students": students_data,
        "specialties": specialties,
        "specialty": specialty,
    }
    return render(request, "students/free_students.html", context)
