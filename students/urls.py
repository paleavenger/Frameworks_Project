from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.students, name="list"),
    path("free/", views.free_students, name="free"),
    path("<int:student_id>/", views.student_detail, name="detail"),
]
