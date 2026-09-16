"""ArenaBook root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ArenaBook Administration"
admin.site.site_title = "ArenaBook Admin"
admin.site.index_title = "Database Management"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("arena.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
