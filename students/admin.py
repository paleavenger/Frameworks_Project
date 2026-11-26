from django.contrib import admin

from homepage.admin_search import CasefoldSearchAdmin
from teams.models import Membership

from .models import Student


# StudentMembershipInline Показывает команду и роль студента
class StudentMembershipInline(admin.TabularInline):
    model = Membership
    fields = ("team", "role")
    readonly_fields = fields
    show_change_link = True
    extra = 0
    can_delete = False

    # has_add_permission Запрещает добавление участия из карточки
    def has_add_permission(self, request, obj=None):
        return False

    # get_queryset Загружает команду и роль вместе с участием
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("team", "role")


# StudentAdmin Настраивает управление студентами
@admin.register(Student)
class StudentAdmin(CasefoldSearchAdmin):
    list_display = ("name", "specialty", "team_name")
    list_filter = ("specialty",)
    search_fields = (
        "name__casefold__contains", "specialty__casefold__contains",
    )
    list_select_related = ("membership__team",)
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (StudentMembershipInline,)

    # team_name Возвращает команду студента
    @admin.display(description="Команда", ordering="membership__team__name")
    def team_name(self, student):
        if hasattr(student, "membership"):
            return student.membership.team
        return None
