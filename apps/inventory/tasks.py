"""
Celery 异步 / 定时任务。
  celery -A config worker -l info
  celery -A config beat -l info
"""
from __future__ import annotations

import logging
import secrets
import string
from datetime import date

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from .db_sync import PasswordSyncError, sync_password_to_database
from .password_log import append_rotated_password

logger = logging.getLogger(__name__)

# 随机密码字符集与长度
PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
PASSWORD_LENGTH = 24


def _generate_password(length: int = PASSWORD_LENGTH) -> str:
    """使用 secrets 生成密码学安全的随机密码。"""
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


@shared_task(name="apps.inventory.tasks.rotate_all_instance_passwords")
def rotate_all_instance_passwords() -> dict:
    """
    每隔 12 小时：遍历全部实例，随机新密码 → 同步真实库 → 加密落库 → 写根目录日志。
    使用MySQL进行示例，暂不支持其他库改密，只记录随机密码
    """
    from .models import DatabaseInstance

    now = timezone.now()
    rotated = 0
    failed = 0

    for instance in DatabaseInstance.objects.all().iterator():
        try:
            plain = _generate_password()
            old_password = instance.get_password()

            # 同步真实数据库（使用MySQL 示例）
            sync_action = sync_password_to_database(instance, old_password, plain)

            instance.set_password(plain)
            instance.last_password_rotated_at = now
            instance.save(
                update_fields=[
                    "password_encrypted",
                    "last_password_rotated_at",
                    "updated_at",
                ]
            )

            # 轮换结果写入项目根目录 rotated_passwords.log
            append_rotated_password(
                instance_id=instance.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
                port=instance.port,
                username=instance.username,
                new_password=plain,
                sync_action=sync_action,
            )

            rotated += 1
            logger.info(
                "已轮换实例密码 instance_id=%s name=%s sync=%s",
                instance.id,
                instance.name,
                sync_action,
            )
        except PasswordSyncError:
            failed += 1
            logger.exception(
                "远程改密失败，未更新本系统 instance_id=%s",
                instance.id,
            )
        except Exception:
            failed += 1
            logger.exception("轮换密码失败 instance_id=%s", instance.id)

    summary = {
        "rotated": rotated,
        "failed": failed,
        "at": now.isoformat(),
        "log_file": "rotated_passwords.log",
    }
    logger.info("密码轮换完成: %s", summary)
    return summary


@shared_task(name="apps.inventory.tasks.collect_daily_instance_stats")
def collect_daily_instance_stats(stat_date_iso: str | None = None) -> dict:
    """
    每天 00:00：按「部门」「集群」两个维度统计实例数，写入 InstanceDailyStat。

    使用 update_or_create，同一天重复跑会覆盖更新。
    """
    from .models import Cluster, DatabaseInstance, Department, InstanceDailyStat

    if stat_date_iso:
        stat_date = date.fromisoformat(stat_date_iso)
    else:
        # Beat 在本地时区 00:00 触发时，统计「当天」
        stat_date = timezone.localdate()

    created_or_updated = 0

    # ---------- 维度 1：按部门 ----------
    dept_counts = {
        row["cluster__department_id"]: row["cnt"]
        for row in DatabaseInstance.objects.values("cluster__department_id").annotate(
            cnt=Count("id")
        )
    }
    for dept in Department.objects.all():
        InstanceDailyStat.objects.update_or_create(
            stat_date=stat_date,
            dimension=InstanceDailyStat.Dimension.DEPARTMENT,
            department=dept,
            cluster=None,
            defaults={"instance_count": dept_counts.get(dept.id, 0)},
        )
        created_or_updated += 1

    # ---------- 维度 2：按集群 ----------
    cluster_counts = {
        row["cluster_id"]: row["cnt"]
        for row in DatabaseInstance.objects.values("cluster_id").annotate(cnt=Count("id"))
    }
    for cluster in Cluster.objects.select_related("department").all():
        InstanceDailyStat.objects.update_or_create(
            stat_date=stat_date,
            dimension=InstanceDailyStat.Dimension.CLUSTER,
            department=cluster.department,
            cluster=cluster,
            defaults={"instance_count": cluster_counts.get(cluster.id, 0)},
        )
        created_or_updated += 1

    summary = {"stat_date": stat_date.isoformat(), "records": created_or_updated}
    logger.info("每日统计完成: %s", summary)
    return summary
