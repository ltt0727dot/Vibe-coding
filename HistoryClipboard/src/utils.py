"""
工具模块 — 统一路径管理 + 配置读写
"""
import os
import sys
import json

# 项目根目录：开发时 = src/ 的父目录，打包后 = exe 所在目录
if getattr(sys, "frozen", False):
    _PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFAULT_SETTINGS = {"retention_days": 3}


def get_data_dir():
    """获取数据根目录（项目本地 data/，非 C 盘）"""
    path = os.path.join(_PROJECT_ROOT, "data")
    os.makedirs(path, exist_ok=True)
    return path


def get_db_path():
    """数据库文件路径"""
    return os.path.join(get_data_dir(), "clipboard.db")


def get_images_dir():
    """图片存储目录"""
    path = os.path.join(get_data_dir(), "images")
    os.makedirs(path, exist_ok=True)
    return path


def get_settings_path():
    """配置文件路径"""
    return os.path.join(get_data_dir(), "settings.json")


def load_settings():
    """读取配置，缺失时返回默认值"""
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并默认值，防止新增字段缺失
            return {**_DEFAULT_SETTINGS, **data}
        except (json.JSONDecodeError, IOError):
            pass
    return dict(_DEFAULT_SETTINGS)


def save_settings(settings: dict):
    """保存配置到文件"""
    path = get_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
