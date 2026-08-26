"""Django Admin：便于本地可视化管理模型数据。"""
from django.contrib import admin

from .models import Cluster, DatabaseInstance, Department, InstanceDailyStat


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "department", "env", "created_at")
    list_filter = ("env", "department")
    search_fields = ("code", "name")


@admin.register(DatabaseInstance)
class DatabaseInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "host",
        "port",
        "db_type",
        "cluster",
        "status",
        "username",
        "last_password_rotated_at",
    )
    list_filter = ("db_type", "status", "cluster")
    search_fields = ("name", "host", "username")
    # 密文与轮换时间只读，避免在 Admin 里误改密文
    readonly_fields = ("password_encrypted", "last_password_rotated_at")


@admin.register(InstanceDailyStat)
class InstanceDailyStatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stat_date",
        "dimension",
        "department",
        "cluster",
        "instance_count",
        "created_at",
    )
    list_filter = ("dimension", "stat_date")
