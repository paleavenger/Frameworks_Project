from django.contrib import admin

from homepage.admin_search import CasefoldSearchAdmin

from .models import Membership, Role, Team


# ReadinessFilter Фильтрует команды по готовности
class ReadinessFilter(admin.SimpleListFilter):
    title = "состояние команды"
    parameter_name = "status"

    # lookups Возвращает варианты состояния команды
    def lookups(self, request, model_admin):
        return Team.Status.choices

    # queryset Применяет выбранный фильтр
    def queryset(self, request, queryset):
        if self.value() in Team.Status.values:
            return queryset.filter(readiness_status=self.value())
        return queryset


# TeamMembershipInline Показывает состав в карточке команды
class TeamMembershipInline(admin.TabularInline):
    model = Membership
    fields = ("student", "role")
    readonly_fields = ("student",)
    show_change_link = True
    extra = 0
    can_delete = False

    # has_add_permission Запрещает добавление участника из карточки
    def has_add_permission(self, request, obj=None):
        return False

    # get_queryset Загружает участников вместе с ролями
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student", "role")


# TeamAdmin Настраивает управление командами
@admin.register(Team)
class TeamAdmin(CasefoldSearchAdmin):
    list_display = ("name", "project", "member_count", "readiness")
    list_filter = ("project", ReadinessFilter)
    search_fields = (
        "name__casefold__contains", "project__title__casefold__contains",
    )
    ordering = ("name", "pk")
    autocomplete_fields = ("project",)
    list_select_related = ("project",)
    list_per_page = 20
    inlines = (TeamMembershipInline,)

    # get_queryset Добавляет к командам статус готовности
    def get_queryset(self, request):
        return super().get_queryset(request).with_readiness_status()

    # member_count Возвращает число участников
    @admin.display(description="Участников", ordering="members_count")
    def member_count(self, team):
        return team.members_count

    # readiness Возвращает подпись статуса готовности
    @admin.display(description="Состояние", ordering="readiness_status")
    def readiness(self, team):
        return Team.Status(team.readiness_status).label


# RoleAdmin Настраивает управление ролями
@admin.register(Role)
class RoleAdmin(CasefoldSearchAdmin):
    list_display = ("name",)
    search_fields = ("name__casefold__contains",)
    ordering = ("name", "pk")
    list_per_page = 20


# MembershipAdmin Настраивает управление составом
@admin.register(Membership)
class MembershipAdmin(CasefoldSearchAdmin):
    list_display = ("student", "team", "project", "role")
    list_editable = ("role",)
    list_filter = ("team", "role")
    search_fields = (
        "student__name__casefold__contains",
        "team__name__casefold__contains",
        "team__project__title__casefold__contains",
    )
    autocomplete_fields = ("student", "team")
    list_select_related = ("student", "team__project", "role")
    ordering = ("team__name", "student__name", "pk")
    list_per_page = 20

    # project Возвращает проект команды участника
    @admin.display(description="Проект", ordering="team__project__title")
    def project(self, membership):
        return membership.team.project
