""" URL：Admin + 业务 API"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # 业务接口前缀 /api/
    path("api/", include("apps.inventory.urls")),
]
