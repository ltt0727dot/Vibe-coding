"""
剪贴板监听模块 — 定时轮询剪贴板变化，自动记录文字和图片
"""
import os
import hashlib
import uuid
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from database import add_item, get_last_hash
from utils import get_images_dir


def _compute_text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()


def _compute_file_hash(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _save_image(qimage: QImage) -> tuple:
    """保存图片和缩略图，返回 (image_path, thumbnail_path)"""
    images_dir = get_images_dir()
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"

    image_path = os.path.join(images_dir, filename)
    qimage.save(image_path, "PNG")

    # 生成缩略图 60x60
    thumb = qimage.scaled(
        60, 60,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    thumb_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_thumb.png"
    thumb_path = os.path.join(images_dir, thumb_name)
    thumb.save(thumb_path, "PNG")

    return image_path, thumb_path


class ClipboardMonitor(QObject):
    """剪贴板监听器：每 500ms 检查剪贴板，发现新内容自动记录"""

    new_item_added = Signal(dict)  # 发射新增记录，供 UI 刷新

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_hash = get_last_hash()
        self._skip_flag = False  # 面板复制后跳过一个轮询周期

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._timer.start(500)

    def skip_next_poll(self):
        """面板复制了内容到剪贴板，标记跳过并锁定当前剪贴板 hash"""
        self._skip_flag = True

    def _check(self):
        if self._skip_flag:
            self._skip_flag = False
            # 计算当前剪贴板内容 hash 并设为 _last_hash，
            # 确保之后所有周期都跳过此内容，直到用户复制新内容
            clipboard = QApplication.clipboard()
            mime = clipboard.mimeData()
            if mime and mime.hasText():
                text = mime.text()
                if text and text.strip():
                    self._last_hash = _compute_text_hash(text)
            return

        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None:
            return

        if mime.hasImage():
            self._handle_image(mime)
        elif mime.hasText():
            text = mime.text()
            if text and text.strip():
                self._handle_text(text)

    def _handle_text(self, text: str):
        content_hash = _compute_text_hash(text)
        if content_hash == self._last_hash:
            return  # 连续相同内容，跳过
        self._last_hash = content_hash
        item_id = add_item("text", content=text, content_hash=content_hash)
        self.new_item_added.emit({
            "id": item_id, "type": "text", "content": text
        })

    def _handle_image(self, mime):
        qimage = mime.imageData()
        if qimage is None or qimage.isNull():
            return
        image_path, thumb_path = _save_image(qimage)
        content_hash = _compute_file_hash(image_path)
        if content_hash == self._last_hash:
            # 相同图片不重复记录，但清理刚保存的文件
            try:
                os.remove(image_path)
                os.remove(thumb_path)
            except OSError:
                pass
            return
        self._last_hash = content_hash
        item_id = add_item(
            "image", image_path=image_path,
            thumbnail_path=thumb_path, content_hash=content_hash
        )
        self.new_item_added.emit({
            "id": item_id, "type": "image",
            "image_path": image_path, "thumbnail_path": thumb_path
        })
