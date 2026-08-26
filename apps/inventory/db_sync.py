"""
按实例数据库类型，将新密码同步到真实数据库。
目前仅实现 MySQL：ALTER USER ... IDENTIFIED BY ...
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# MySQL 用户名只允许字母数字下划线，防止 SQL 注入
_MYSQL_USER_RE = re.compile(r"^[A-Za-z0-9_]+$")


class PasswordSyncError(Exception):
    """远程库改密失败。"""


def sync_password_to_database(instance, old_password: str, new_password: str) -> str:
    """
    按 db_type 调用对应改密逻辑
    """
    from .models import DatabaseInstance

    if instance.db_type == DatabaseInstance.DbType.MYSQL:
        if not instance.username:
            return "skipped_no_username"
        alter_mysql_user_password(
            host=instance.host,
            port=instance.port,
            username=instance.username,
            old_password=old_password,
            new_password=new_password,
        )
        return "mysql_alter_user"

    return "skipped_unsupported"


def alter_mysql_user_password(
        host: str,
        port: int,
        username: str,
        old_password: str,
        new_password: str,
        user_host: str = "%",
    ) -> None:
    """
    连接 MySQL，用旧密码鉴权后执行 ALTER USER 改密。
    """
    import pymysql

    if not _MYSQL_USER_RE.match(username):
        raise PasswordSyncError(f"MySQL 用户名非法: {username!r}")

    if not user_host.replace("%", "").replace("_", "").isalnum() and user_host not in ("%", "localhost"):
        raise PasswordSyncError(f"MySQL user host 非法: {user_host!r}")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=old_password,
            connect_timeout=10,
            charset="utf8mb4",
        )
    except pymysql.Error as exc:
        raise PasswordSyncError(f"MySQL 连接失败 {host}:{port}: {exc}") from exc

    try:
        with conn.cursor() as cursor:
            # 用户名/host 已校验；密码走参数化
            cursor.execute(
                f"ALTER USER `{username}`@`{user_host}` IDENTIFIED BY %s",
                (new_password,),
            )
            cursor.execute("FLUSH PRIVILEGES")
        conn.commit()
        logger.info(
            "MySQL ALTER USER 成功 host=%s port=%s user=%s",
            host,
            port,
            username,
        )
    except pymysql.Error as exc:
        raise PasswordSyncError(f"MySQL ALTER USER 失败: {exc}") from exc
    finally:
        conn.close()
