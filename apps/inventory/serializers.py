"""
DRF 序列化器
"""
from rest_framework import serializers

from .models import Cluster, DatabaseInstance, Department, InstanceDailyStat


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化。"""

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "code",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ClusterSerializer(serializers.ModelSerializer):
    """集群序列化"""

    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Cluster
        fields = (
            "id",
            "name",
            "code",
            "department",
            "department_name",
            "env",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "department_name")


class DatabaseInstanceSerializer(serializers.ModelSerializer):
    """
    实例序列化
    """

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="明文密码，仅写入时使用，入库前加密",
    )
    cluster_name = serializers.CharField(source="cluster.name", read_only=True)
    department_id = serializers.IntegerField(source="cluster.department_id", read_only=True)
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = DatabaseInstance
        fields = (
            "id",
            "name",
            "host",
            "port",
            "db_type",
            "cluster",
            "cluster_name",
            "department_id",
            "status",
            "username",
            "password",
            "has_password",
            "last_password_rotated_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "has_password",
            "last_password_rotated_at",
            "created_at",
            "updated_at",
            "cluster_name",
            "department_id",
        )

    def get_has_password(self, obj: DatabaseInstance) -> bool:
        return bool(obj.password_encrypted)

    def create(self, validated_data):
        # 取出明文密码，不直接写到模型字段
        plain = validated_data.pop("password", "")
        instance = DatabaseInstance(**validated_data)
        if plain:
            instance.set_password(plain)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        plain = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # 仅当请求显式带了 password 才更新
        if plain is not None:
            instance.set_password(plain)
        instance.save()
        return instance


class InstanceDailyStatSerializer(serializers.ModelSerializer):
    """每日统计只读序列化。"""

    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
        allow_null=True,
    )
    cluster_name = serializers.CharField(
        source="cluster.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = InstanceDailyStat
        fields = (
            "id",
            "stat_date",
            "dimension",
            "department",
            "department_name",
            "cluster",
            "cluster_name",
            "instance_count",
            "created_at",
        )
        read_only_fields = fields


class ProbeResultSerializer(serializers.Serializer):
    """TCP 探测结果结构"""

    instance_id = serializers.IntegerField()
    host = serializers.CharField()
    port = serializers.IntegerField()
    reachable = serializers.BooleanField()
    latency_ms = serializers.FloatField(allow_null=True)
    error = serializers.CharField(allow_null=True, allow_blank=True)
