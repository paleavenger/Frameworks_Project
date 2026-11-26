from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.projects, name="list"),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("p/<str:slug>/", views.project_detail, name="by_slug"),
    path("<int:project_id>/image/", views.project_image, name="image"),
]
