from django.contrib import admin
from django.db.models import Count

from homepage.admin_search import CasefoldSearchAdmin
from teams.models import Team

from .forms import ProjectImageForm
from .models import Project


# ProjectTeamInline Показывает команды в карточке проекта
class ProjectTeamInline(admin.TabularInline):
    model = Team
    fields = ("name",)
    readonly_fields = fields
    show_change_link = True
    extra = 0
    can_delete = False

    # has_add_permission Запрещает добавление команд из карточки
    def has_add_permission(self, request, obj=None):
        return False


# ProjectAdmin Настраивает управление проектами
@admin.register(Project)
class ProjectAdmin(CasefoldSearchAdmin):
    form = ProjectImageForm
    fields = ("title", "image", "slug")
    list_display = ("id", "title", "team_count")
    list_display_links = ("id", "title")
    search_fields = ("title__casefold__contains", "slug")
    ordering = ("title", "pk")
    readonly_fields = ("slug",)
    list_per_page = 20
    inlines = (ProjectTeamInline,)

    # get_queryset Дополняет проекты числом команд
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(team_total=Count("teams"))

    # team_count Возвращает число команд проекта
    @admin.display(description="Команд", ordering="team_total")
    def team_count(self, project):
        return project.team_total
