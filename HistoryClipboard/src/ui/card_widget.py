"""
剪贴板卡片组件 — 单条记录展示
"""
from datetime import datetime

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                                QPushButton, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

PURPLE = "#7B61FF"
PURPLE_BG = "#EDE5FF"


def _format_time(ts_str):
    """将时间戳转为可读的相对时间"""
    try:
        dt = datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return ts_str or ""
    now = datetime.now()
    diff = now - dt
    if diff.days > 0:
        return f"{diff.days}天前"
    if diff.seconds >= 3600:
        return f"{diff.seconds // 3600}小时前"
    if diff.seconds >= 60:
        return f"{diff.seconds // 60}分钟前"
    return "刚刚"


class ClipboardCard(QFrame):
    """单条剪贴板记录卡片"""

    clicked = Signal(dict)        # 点击卡片 → 复制
    pin_toggled = Signal(int)     # 置顶切换 → item_id
    delete_requested = Signal(int)  # 删除 → item_id

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._item = item
        self.setObjectName("clipboardCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 根据置顶状态设置样式类
        if item.get("pinned"):
            self.setProperty("pinned", True)

        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 8, 8)
        root.setSpacing(8)

        # ---- 内容区 ----
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        if self._item["type"] == "image":
            # 图片卡片：缩略图 + 标签
            thumb_path = self._item.get("thumbnail_path") or self._item.get("image_path")
            thumb_label = QLabel()
            if thumb_path:
                pixmap = QPixmap(thumb_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    thumb_label.setPixmap(pixmap)
            thumb_label.setFixedSize(48, 48)
            thumb_label.setStyleSheet("background: #f0f0f0; border-radius: 4px;")
            root.addWidget(thumb_label)

            label = QLabel("[图片]")
            label.setStyleSheet("color: #8c8c8c; font-size: 13px;")
            content_layout.addWidget(label)
        else:
            # 文字卡片：内容预览
            text = self._item.get("content", "")
            label = QLabel(text)
            label.setWordWrap(True)
            label.setMaximumHeight(40)
            label.setStyleSheet("color: #1f1f1f; font-size: 12px;")
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            content_layout.addWidget(label)

        # 时间戳
        ts_label = QLabel(_format_time(self._item.get("created_at", "")))
        ts_label.setStyleSheet("color: #8c8c8c; font-size: 10px;")
        content_layout.addWidget(ts_label)

        root.addLayout(content_layout, 1)

        # ---- 操作按钮 ----
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)

        pin_btn = QPushButton()
        pin_btn.setFixedSize(24, 24)
        pin_btn.setText("📌" if self._item.get("pinned") else "📍")
        pin_btn.setToolTip("置顶" if not self._item.get("pinned") else "取消置顶")
        pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pin_btn.clicked.connect(self._on_pin)
        pin_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; font-size: 12px; }"
            "QPushButton:hover { background: #f0e8ff; border-radius: 4px; }"
        )
        btn_layout.addWidget(pin_btn)

        del_btn = QPushButton()
        del_btn.setFixedSize(24, 24)
        del_btn.setText("✕")
        del_btn.setToolTip("删除")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self._on_delete)
        del_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #999; font-size: 12px; }"
            "QPushButton:hover { background: #fff0f0; color: #ff4d4f; border-radius: 4px; }"
        )
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()

        root.addLayout(btn_layout)

    def _update_style(self):
        base = (
            "ClipboardCard {"
            "  background: #ffffff;"
            "  border: 1px solid #e8e8e8;"
            "  border-radius: 8px;"
            "  margin: 3px 8px;"
            "}"
            f"ClipboardCard:hover {{ border-color: {PURPLE}; }}"
        )
        if self._item.get("pinned"):
            self.setStyleSheet(
                base
                + "ClipboardCard[pinned=\"true\"] {"
                f"  background: {PURPLE_BG};"
                f"  border-left: 3px solid {PURPLE};"
                "}"
            )
        else:
            self.setStyleSheet(base)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._item)
        super().mousePressEvent(event)

    def _on_pin(self):
        self.pin_toggled.emit(self._item["id"])

    def _on_delete(self):
        self.delete_requested.emit(self._item["id"])
