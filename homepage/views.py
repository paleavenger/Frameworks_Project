"""Главная страница и общие функции веб-интерфейса."""

from functools import wraps
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from storage import AppData, load_data


def with_data(
    view: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Декоратор: загружает данные проекта и передаёт их в view-функцию.

    Если файлы данных повреждены, показывает страницу ошибки с кодом 500.
    """

    @wraps(view)
    def wrapper(
        request: HttpRequest,
        *args: object,
        **kwargs: object,
    ) -> HttpResponse:
        try:
            data = load_data()
        except (RuntimeError, ValueError) as error:
            return render(
                request,
                "homepage/data_error.html",
                {"error": str(error)},
                status=500,
            )
        return view(request, data, *args, **kwargs)

    return wrapper


@with_data
def index(request: HttpRequest, data: AppData) -> HttpResponse:
    """Главная страница: описание приложения и переходы к разделам."""
    context = {
        "students": data.students,
        "teams": data.teams,
        "projects": data.projects,
    }
    return render(request, "homepage/index.html", context)


def page_not_found(
    request: HttpRequest,
    exception: Exception,
) -> HttpResponse:
    """Обработчик 404 для любого адреса без маршрута."""
    return render(request, "404.html", status=404)
