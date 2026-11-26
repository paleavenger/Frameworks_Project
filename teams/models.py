from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Greatest
from django.urls import reverse

from models.teams import Team as ConsoleTeam


# TeamQuerySet Дополняет запросы к командам
class TeamQuerySet(models.QuerySet):
    # with_member_counts Добавляет число участников и ролей
    def with_member_counts(self):
        return self.annotate(
            members_count=models.Count("memberships"),
            roles_count=models.Count("memberships__role"),
        )

    # with_readiness_status Добавляет статус готовности
    def with_readiness_status(self):
        return self.with_member_counts().annotate(
            readiness_status=models.Case(
                models.When(
                    members_count=0, then=models.Value(Team.Status.EMPTY),
                ),
                models.When(
                    members_count__gte=Team.MIN_SIZE,
                    roles_count=models.F("members_count"),
                    then=models.Value(Team.Status.READY),
                ),
                default=models.Value(Team.Status.FORMING),
            ),
        )

    # with_readiness Добавляет процент готовности
    def with_readiness(self):
        return self.with_readiness_status().annotate(
            readiness_percent=models.ExpressionWrapper(
                models.F("roles_count") * 100
                / Greatest(models.F("members_count"), Team.MIN_SIZE),
                output_field=models.IntegerField(),
            ),
        )

    # with_vacancies Отбирает команды со свободными местами
    def with_vacancies(self, places):
        return self.annotate(
            members_count=models.Count("memberships"),
        ).annotate(
            free_places=Team.MAX_SIZE - models.F("members_count"),
        ).filter(free_places__gte=places)


# Team Хранит проект и состав команды
class Team(models.Model):
    # Status Задаёт состояния готовности команды
    class Status(models.TextChoices):
        EMPTY = "empty", "Пустая"
        FORMING = "forming", "Формируется"
        READY = "ready", "Готова к работе"

    MIN_SIZE = ConsoleTeam.MIN_SIZE
    MAX_SIZE = ConsoleTeam.MAX_SIZE

    name = models.TextField("название")
    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="teams",
        verbose_name="проект",
    )
    students = models.ManyToManyField(
        "students.Student", through="Membership", related_name="teams",
        verbose_name="студенты",
    )

    objects = TeamQuerySet.as_manager()

    # Meta Задаёт подписи модели команды
    class Meta:
        verbose_name = "команда"
        verbose_name_plural = "команды"

    # get_absolute_url Возвращает адрес команды
    def get_absolute_url(self):
        return reverse("teams:detail", kwargs={"team_id": self.pk})

    # __str__ Возвращает название команды
    def __str__(self) -> str:
        return self.name

    # readiness_message Формирует сообщение о готовности
    @property
    def readiness_message(self) -> str:
        if self.members_count == 0:
            return "Команда пока пуста"
        if self.members_count < self.MIN_SIZE:
            return f"Нужно не менее {self.MIN_SIZE} участников"
        if self.roles_count < self.members_count:
            return "Нужно назначить роли"
        return "Команда готова к работе"


# Role Хранит роль в команде
class Role(models.Model):
    name = models.TextField("название", unique=True)

    # Meta Задаёт подписи модели роли
    class Meta:
        verbose_name = "роль"
        verbose_name_plural = "роли"

    # __str__ Возвращает название роли
    def __str__(self) -> str:
        return self.name


# Membership Связывает студента, команду и роль
class Membership(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="memberships",
        verbose_name="команда",
    )
    student = models.OneToOneField(
        "students.Student", on_delete=models.CASCADE,
        related_name="membership", verbose_name="студент",
    )
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="memberships",
        null=True, blank=True, verbose_name="роль",
        help_text="Оставьте поле пустым, если роль ещё не назначена.",
    )

    # Meta Задаёт подписи модели участия
    class Meta:
        verbose_name = "участие в команде"
        verbose_name_plural = "состав команд"

    # __str__ Возвращает студента и его команду
    def __str__(self) -> str:
        return f"{self.student} — {self.team}"

    # clean Проверяет лимит участников команды
    def clean(self):
        super().clean()
        if self.team_id is None:
            return
        others = Membership.objects.filter(team_id=self.team_id)
        if self.pk is not None:
            others = others.exclude(pk=self.pk)
        if others.count() >= Team.MAX_SIZE:
            message = f"В команде не более {Team.MAX_SIZE} участников"
            raise ValidationError(
                {"team": message},
            )
