from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("students/", include("students.urls")),
    path("teams/", include("teams.urls")),
    path("projects/", include("projects.urls")),
    path("statistics/", include("stats.urls")),
]

handler404 = "homepage.views.page_not_found"

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()

admin.site.site_header = "Управление учебными проектными командами"
admin.site.site_title = "Управление командами"
admin.site.index_title = "Данные проекта"
