"""
Celery 应用入口。
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
# namespace="CELERY" → 读取 CELERY_BROKER_URL、CELERY_BEAT_SCHEDULE 等
app.config_from_object("django.conf:settings", namespace="CELERY")
# 自动发现各 INSTALLED_APPS 下的 tasks.py
app.autodiscover_tasks()
