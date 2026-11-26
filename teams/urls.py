from django.urls import path

from . import views

app_name = "teams"

urlpatterns = [
    path("", views.teams, name="list"),
    path("vacancies/", views.team_vacancies, name="vacancies"),
    path("<int:team_id>/", views.team_detail, name="detail"),
    path(
        "<int:team_id>/members/add/", views.membership_create,
        name="membership_create",
    ),
    path(
        "<int:team_id>/members/<int:membership_id>/edit/",
        views.membership_update, name="membership_update",
    ),
    path(
        "<int:team_id>/members/<int:membership_id>/remove/",
        views.membership_remove, name="membership_remove",
    ),
]
