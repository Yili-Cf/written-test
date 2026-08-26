"""
Fernet 对称加解密工具：保护 DatabaseInstance 的管理密码。
密钥来源：settings.FERNET_KEY
开发未配置时会临时生成一把密钥
"""
from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)

# 进程内单例，避免重复构造 Fernet
_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    """获取（或懒加载）全局 Fernet 实例。"""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = (settings.FERNET_KEY or "").strip()
    if not key:
        key = Fernet.generate_key().decode()
        logger.warning(
            "FERNET_KEY 未配置，已临时生成开发用密钥。"
            "重启后已加密密码将无法解密，生产环境请固定配置 FERNET_KEY。"
        )
        settings.FERNET_KEY = key

    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_password(plain: str) -> str:
    """明文密码 → URL-safe Base64 密文字符串。"""
    if plain is None:
        raise ValueError("password cannot be None")
    token = get_fernet().encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_password(token: str) -> str:
    """密文字符串 → 明文密码。密钥不一致时抛 ValueError。"""
    if not token:
        return ""
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("无法解密密码，请检查 FERNET_KEY 是否与加密时一致") from exc
