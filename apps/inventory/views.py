"""
DRF 视图
"""
import socket
import time

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cluster, DatabaseInstance, Department, InstanceDailyStat
from .serializers import (
    ClusterSerializer,
    DatabaseInstanceSerializer,
    DepartmentSerializer,
    InstanceDailyStatSerializer,
    ProbeResultSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门增删改查：/api/departments/"""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filterset_fields = ("code",)
    search_fields = ("name", "code")


class ClusterViewSet(viewsets.ModelViewSet):
    """集群增删改查：/api/clusters/"""

    queryset = Cluster.objects.select_related("department").all()
    serializer_class = ClusterSerializer
    filterset_fields = ("department", "env", "code")
    search_fields = ("name", "code")


class DatabaseInstanceViewSet(viewsets.ModelViewSet):
    """实例增删改查：/api/instances/；探测：GET|POST /api/instances/{id}/probe/"""

    queryset = DatabaseInstance.objects.select_related(
        "cluster",
        "cluster__department",
    ).all()
    serializer_class = DatabaseInstanceSerializer
    filterset_fields = ("cluster", "db_type", "status")
    search_fields = ("name", "host")

    @action(detail=True, methods=["get", "post"], url_path="probe")
    def probe(self, request, pk=None):
        """
        探测该实例 host:port 的 TCP 是否可达。

        GET  ?timeout=3
        POST {"timeout": 3}
        """
        instance = self.get_object()
        if request.method == "GET":
            timeout = float(request.query_params.get("timeout", 3.0))
        else:
            timeout = float(request.data.get("timeout", 3.0))
        result = probe_tcp(instance.host, instance.port, timeout=timeout)
        payload = {
            "instance_id": instance.id,
            "host": instance.host,
            "port": instance.port,
            **result,
        }
        serializer = ProbeResultSerializer(payload)
        return Response(serializer.data)


class InstanceDailyStatViewSet(viewsets.ReadOnlyModelViewSet):
    """每日统计只读查询：/api/stats/"""

    queryset = InstanceDailyStat.objects.select_related(
        "department",
        "cluster",
    ).all()
    serializer_class = InstanceDailyStatSerializer
    filterset_fields = ("stat_date", "dimension", "department", "cluster")


class ProbeByAddressAPIView(APIView):
    """
    POST /api/probe/  {"host":"127.0.0.1","port":3306,"timeout":3}
    """

    def post(self, request):
        host = request.data.get("host")
        port = request.data.get("port")
        if not host or port is None:
            return Response(
                {"detail": "host 与 port 必填"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            port = int(port)
        except (TypeError, ValueError):
            return Response(
                {"detail": "port 必须为整数"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        timeout = float(request.data.get("timeout", 3.0))
        result = probe_tcp(host, port, timeout=timeout)
        return Response({"host": host, "port": port, **result})


def probe_tcp(host: str, port: int, timeout: float = 3.0) -> dict:
    """
    使用 socket.create_connection 做 TCP 三次握手探测。
    返回：
      reachable: 是否连通
      latency_ms: 建连耗时（毫秒）
      error: 失败时的错误信息
    """
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = (time.perf_counter() - start) * 1000
            return {
                "reachable": True,
                "latency_ms": round(latency_ms, 2),
                "error": None,
            }
    except OSError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "reachable": False,
            "latency_ms": round(latency_ms, 2),
            "error": str(exc),
        }
