"""
URL configuration for task_management_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/rules/', include('apps.rules.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
