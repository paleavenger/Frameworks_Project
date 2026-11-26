from functools import wraps
from typing import Callable

from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from projects.models import Project
from students.models import Student
from teams.models import Team


# with_db Обрабатывает ошибки базы данных
def with_db(
    view: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    # wrapper Вызывает представление с обработкой ошибок базы
    @wraps(view)
    def wrapper(
        request: HttpRequest,
        *args: object,
        **kwargs: object,
    ) -> HttpResponse:
        try:
            return view(request, *args, **kwargs)
        except DatabaseError as error:
            return render(
                request,
                "homepage/data_error.html",
                {"error": str(error)},
                status=500,
            )

    return wrapper


# index Показывает главную страницу со сводкой
@with_db
def index(request: HttpRequest) -> HttpResponse:
    counts = {
        "students_count": Student.objects.count(),
        "teams_count": Team.objects.count(),
        "projects_count": Project.objects.count(),
    }
    return render(request, "homepage/index.html", {"counts": counts})


# page_not_found Показывает страницу 404
def page_not_found(
    request: HttpRequest,
    exception: Exception,
) -> HttpResponse:
    return render(request, "404.html", status=404)
