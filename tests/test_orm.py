from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.db.models import ProtectedError

from students.models import Student
from teams.models import Membership, Team


def test_import_preserves_links_and_source(orm_database, data_dir):
    source = data_dir / "teams.sqlite"
    before = source.read_bytes()
    call_command("import_pr7", source=source, stdout=StringIO())
    assert source.read_bytes() == before
    membership = Membership.objects.get(student_id=1)
    assert membership.student.membership == membership
    assert membership.role.name == "аналитик"
    assert membership.team.project.title == "Журнал"
    assert membership.team.students.get() == membership.student
    assert Membership.objects.count() == 1

    Student.objects.filter(pk=1).update(name="Новое имя")
    with pytest.raises(CommandError, match="Конфликт данных"):
        call_command("import_pr7", source=source, stdout=StringIO())
    assert Student.objects.get(pk=1).name == "Новое имя"


def test_membership_crud_and_deletion_policy(orm_database):
    team = Team.objects.get(pk=1)
    membership = Membership.objects.create(team=team, student_id=2)
    with pytest.raises(IntegrityError):
        Membership.objects.create(team=team, student_id=2)
    with pytest.raises(ProtectedError):
        team.project.delete()

    membership.role_id = 1
    membership.save(update_fields=["role"])
    membership.refresh_from_db()
    assert membership.role.name == "аналитик"
    team.delete()
    assert not Membership.objects.filter(pk=membership.pk).exists()
    assert Student.objects.filter(pk=2).exists()


def test_membership_capacity_applies_to_insert_and_transfer(orm_database):
    team = Team.objects.get(pk=1)
    for student_id in (2, 3, 4):
        Membership.objects.create(team=team, student_id=student_id)
    fifth = Student.objects.create(name="Пятый")
    Membership.objects.create(team=team, student=fifth)
    sixth = Student.objects.create(name="Шестой")
    with pytest.raises(IntegrityError, match="не более 5"):
        Membership.objects.create(team=team, student=sixth)

    other_team = Team.objects.create(name="Бета", project=team.project)
    member = Membership.objects.create(team=other_team, student=sixth)
    with pytest.raises(IntegrityError, match="не более 5"):
        Membership.objects.filter(pk=member.pk).update(team=team)
    member.refresh_from_db()
    assert member.team == other_team
