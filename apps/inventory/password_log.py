"""
密码轮换结果写入项目根目录明文日志（便于运维接管）。
文件路径：项目根目录 / rotated_passwords.log
"""
from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

LOG_FILENAME = "rotated_passwords.log"


def get_rotation_log_path() -> Path:
    """轮换密码日志文件：项目根目录。"""
    return Path(settings.BASE_DIR) / LOG_FILENAME


def append_rotated_password(
    *,
    instance_id: int,
    instance_name: str,
    db_type: str,
    host: str,
    port: int,
    username: str,
    new_password: str,
    sync_action: str,
) -> None:
    """追加一行轮换记录（含明文新密码）。"""
    path = get_rotation_log_path()
    ts = timezone.localtime().isoformat(timespec="seconds")
    line = (
        f"{ts}\tinstance_id={instance_id}\tname={instance_name}\t"
        f"db_type={db_type}\thost={host}\tport={port}\t"
        f"username={username}\tpassword={new_password}\tsync={sync_action}\n"
    )
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        logger.info("轮换密码已写入 %s instance_id=%s", path, instance_id)
    except OSError:
        logger.exception("写入轮换密码日志失败 path=%s", path)
        raise
