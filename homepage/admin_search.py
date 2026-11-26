from django.contrib import admin

from . import lookups  # noqa: F401


# CasefoldSearchAdmin Поддерживает поиск без учёта регистра
class CasefoldSearchAdmin(admin.ModelAdmin):
    # get_search_results Нормализует регистр поискового запроса
    def get_search_results(self, request, queryset, search_term):
        return super().get_search_results(
            request, queryset, search_term.casefold(),
        )
