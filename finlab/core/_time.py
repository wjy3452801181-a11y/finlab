"""时区常量 — 零依赖，避免循环导入"""
from datetime import timedelta, timezone

BJT = timezone(timedelta(hours=8))
