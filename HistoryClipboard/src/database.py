"""
数据层模块 — SQLite 操作封装
线程安全：所有写操作持有全局锁
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from utils import get_db_path

_lock = threading.Lock()


def _get_conn():
    """创建新连接，启用 WAL 模式提升并发性能"""
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表（如不存在）"""
    with _lock:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT,
                image_path TEXT,
                thumbnail_path TEXT,
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pinned INTEGER DEFAULT 0,
                pinned_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()


def add_item(item_type, content=None, image_path=None,
             thumbnail_path=None, content_hash=None):
    """新增一条记录，返回新记录的 id"""
    with _lock:
        conn = _get_conn()
        cursor = conn.execute(
            """INSERT INTO clipboard_items
               (type, content, image_path, thumbnail_path, content_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_type, content, image_path, thumbnail_path, content_hash,
             datetime.now().isoformat())
        )
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id


def get_items(search=None, limit=100, offset=0):
    """
    获取记录列表：置顶项在前（按 pinned_at 倒序），
    普通项在后（按 created_at 倒序）
    search 参数对文字记录做模糊匹配
    """
    with _lock:
        conn = _get_conn()
        if search:
            search_pattern = f"%{search}%"
            rows = conn.execute(
                """SELECT * FROM clipboard_items
                   WHERE (type = 'text' AND content LIKE ?)
                      OR (type = 'image')
                   ORDER BY pinned DESC, pinned_at DESC, created_at DESC
                   LIMIT ? OFFSET ?""",
                (search_pattern, limit, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM clipboard_items
                   ORDER BY pinned DESC, pinned_at DESC, created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


def get_last_hash():
    """获取最新一条记录的 content_hash，用于去重"""
    with _lock:
        conn = _get_conn()
        row = conn.execute(
            "SELECT content_hash FROM clipboard_items ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return row["content_hash"] if row else None


def toggle_pin(item_id: int) -> bool:
    """切换置顶状态，返回新状态"""
    with _lock:
        conn = _get_conn()
        row = conn.execute(
            "SELECT pinned FROM clipboard_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            conn.close()
            return False
        new_pinned = 0 if row["pinned"] else 1
        pinned_at = datetime.now().isoformat() if new_pinned else None
        conn.execute(
            "UPDATE clipboard_items SET pinned = ?, pinned_at = ? WHERE id = ?",
            (new_pinned, pinned_at, item_id)
        )
        conn.commit()
        conn.close()
        return bool(new_pinned)


def delete_item(item_id: int) -> Optional[dict]:
    """删除记录，返回被删记录信息（用于清理图片文件）"""
    with _lock:
        conn = _get_conn()
        row = conn.execute(
            "SELECT * FROM clipboard_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            conn.close()
            return None
        info = dict(row)
        conn.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return info


def cleanup_expired(retention_days: int):
    """
    清理超过 retention_days 天且未置顶的记录
    返回被删记录列表（用于清理对应图片文件）
    """
    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM clipboard_items WHERE pinned = 0 AND created_at < ?",
            (cutoff,)
        ).fetchall()
        deleted = [dict(r) for r in rows]
        if deleted:
            ids = [r["id"] for r in rows]
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"DELETE FROM clipboard_items WHERE id IN ({placeholders})",
                ids
            )
            conn.commit()
        conn.close()
        return deleted


def get_total_count():
    """获取总记录数"""
    with _lock:
        conn = _get_conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM clipboard_items").fetchone()
        conn.close()
        return row["cnt"]
