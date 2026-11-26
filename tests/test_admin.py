import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client
from django.urls import reverse

from teams.models import Membership, Team


@pytest.fixture
def admin_client(orm_database):
    user = get_user_model().objects.create_superuser(username="test_admin")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.parametrize("model_url", (
    "projects_project", "students_student", "teams_team", "teams_membership",
    "teams_role",
))
def test_admin_lists_are_accessible(admin_client, model_url):
    response = admin_client.get(reverse(f"admin:{model_url}_changelist"))
    assert response.status_code == 200
    assert response.context["cl"].result_count > 0


def test_admin_search_and_filter_use_related_data(admin_client):
    response = admin_client.get(reverse("admin:teams_team_changelist"), {
        "q": "ЖУРНАЛ", "status": Team.Status.FORMING,
    })
    assert [team.name for team in response.context["cl"].result_list] == [
        "Альфа",
    ]
    response = admin_client.get(reverse("admin:teams_membership_changelist"), {
        "q": "АННА АЛЬФА", "role__id__exact": 1,
    })
    assert [member.student.name for member in (
        response.context["cl"].result_list
    )] == ["Анна"]


def test_admin_changes_role_in_team_inline(admin_client):
    address = reverse("admin:teams_team_change", args=[1])
    response = admin_client.get(address)
    inline = response.context["inline_admin_formsets"][0].formset
    assert inline.initial_form_count() == 1
    public_link = response.context["absolute_url"]
    assert admin_client.get(public_link).url.endswith("/teams/1/")

    response = admin_client.post(address, {
        "name": "Альфа", "project": 1,
        "memberships-TOTAL_FORMS": 1,
        "memberships-INITIAL_FORMS": 1,
        "memberships-MIN_NUM_FORMS": 0,
        "memberships-MAX_NUM_FORMS": 0,
        "memberships-0-id": 1,
        "memberships-0-team": 1,
        "memberships-0-role": 2,
    })
    assert response.status_code == 302
    assert Membership.objects.get(pk=1).role_id == 2


def test_admin_respects_group_permissions(orm_database):
    client = Client()
    listing = reverse("admin:students_student_changelist")
    assert client.get(listing).status_code == 302
    staff = get_user_model().objects.create_user(
        username="reader", is_staff=True,
    )
    readers = Group.objects.create(name="Просмотр студентов")
    readers.permissions.add(Permission.objects.get(
        content_type__app_label="students", codename="view_student",
    ))
    staff.groups.add(readers)
    client.force_login(staff)
    assert client.get(listing).status_code == 200
    assert client.get(reverse("admin:students_student_add")).status_code == 403
    teams = reverse("admin:teams_team_changelist")
    assert client.get(teams).status_code == 403
