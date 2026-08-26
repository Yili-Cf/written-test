"""
业务 App 路由。
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClusterViewSet,
    DatabaseInstanceViewSet,
    DepartmentViewSet,
    InstanceDailyStatViewSet,
    ProbeByAddressAPIView,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("clusters", ClusterViewSet, basename="cluster")
router.register("instances", DatabaseInstanceViewSet, basename="instance")
router.register("stats", InstanceDailyStatViewSet, basename="stat")

urlpatterns = [
    path("", include(router.urls)),
    # 按任意地址探测：POST /api/probe/
    path("probe/", ProbeByAddressAPIView.as_view(), name="probe-by-address"),
]
