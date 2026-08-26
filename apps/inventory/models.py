"""
业务数据模型
"""
from django.db import models

from .crypto import decrypt_password, encrypt_password


class Department(models.Model):
    """企业内部部门。"""

    name = models.CharField("部门名称", max_length=128, unique=True)
    code = models.CharField("部门编码", max_length=64, unique=True)
    description = models.TextField("描述", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Cluster(models.Model):
    """数据库集群，隶属于某个部门。"""

    class Env(models.TextChoices):
        DEV = "dev", "开发"
        TEST = "test", "测试"
        PROD = "prod", "生产"

    name = models.CharField("集群名称", max_length=128)
    code = models.CharField("集群编码", max_length=64, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,  # 有集群时禁止删部门
        related_name="clusters",
        verbose_name="所属部门",
    )
    env = models.CharField(
        "环境",
        max_length=16,
        choices=Env.choices,
        default=Env.DEV,
    )
    description = models.TextField("描述", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "集群"
        verbose_name_plural = "集群"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class DatabaseInstance(models.Model):
    """
    被管理的数据库实例（元数据 + 管理账号）。

    密码不以明文存储：通过 set_password / get_password 做 Fernet 加解密。
    """

    class DbType(models.TextChoices):
        MYSQL = "mysql", "MySQL"
        POSTGRESQL = "postgresql", "PostgreSQL"
        REDIS = "redis", "Redis"
        MONGODB = "mongodb", "MongoDB"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        RUNNING = "running", "运行中"
        STOPPED = "stopped", "已停止"
        UNKNOWN = "unknown", "未知"

    name = models.CharField("实例名称", max_length=128)
    host = models.CharField("主机", max_length=255)
    port = models.PositiveIntegerField("端口", default=3306)
    db_type = models.CharField(
        "数据库类型",
        max_length=32,
        choices=DbType.choices,
        default=DbType.MYSQL,
    )
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.PROTECT,
        related_name="instances",
        verbose_name="所属集群",
    )
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.UNKNOWN,
    )
    username = models.CharField("管理账号", max_length=128, blank=True, default="")
    # Fernet 加密后的密文字符串（非明文）
    password_encrypted = models.TextField("加密密码", blank=True, default="")
    last_password_rotated_at = models.DateTimeField(
        "上次密码轮换时间",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "数据库实例"
        verbose_name_plural = "数据库实例"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["host", "port"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.host}:{self.port})"

    def set_password(self, plain: str) -> None:
        """明文 → 加密后写入 password_encrypted。"""
        self.password_encrypted = encrypt_password(plain) if plain else ""

    def get_password(self) -> str:
        """解密 password_encrypted → 明文"""
        if not self.password_encrypted:
            return ""
        return decrypt_password(self.password_encrypted)

    @property
    def department(self) -> Department:
        """经集群反查所属部门"""
        return self.cluster.department


class InstanceDailyStat(models.Model):
    """
    每日实例数量统计快照。
    dimension=department：按部门汇总
    dimension=cluster：按集群汇总
    """

    class Dimension(models.TextChoices):
        DEPARTMENT = "department", "按部门"
        CLUSTER = "cluster", "按集群"

    stat_date = models.DateField("统计日期", db_index=True)
    dimension = models.CharField(
        "统计维度",
        max_length=16,
        choices=Dimension.choices,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="daily_stats",
        null=True,
        blank=True,
        verbose_name="部门",
    )
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        related_name="daily_stats",
        null=True,
        blank=True,
        verbose_name="集群",
    )
    instance_count = models.PositiveIntegerField("实例数量", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "实例每日统计"
        verbose_name_plural = "实例每日统计"
        ordering = ["-stat_date", "dimension"]
        # 同一天、同一维度、同一部门/集群只保留一条，避免重复统计
        constraints = [
            models.UniqueConstraint(
                fields=["stat_date", "dimension", "department", "cluster"],
                name="uniq_daily_stat_dimension",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.stat_date} {self.dimension} count={self.instance_count}"
