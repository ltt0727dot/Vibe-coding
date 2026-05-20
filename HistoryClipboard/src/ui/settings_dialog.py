"""
设置对话框 — 存储期限选择
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor

from utils import load_settings, save_settings

TEXT_COLOR = "#612A8A"
BG_R, BG_G, BG_B = 184, 137, 219  # #B889DB
BG_ALPHA = 115                      # 55%透明


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(300, 180)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._settings = load_settings()
        self._setup_ui()

    def paintEvent(self, event):
        """手绘半透明紫色背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(BG_R, BG_G, BG_B, BG_ALPHA))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

    def _setup_ui(self):
        self.setObjectName("settingsDialog")
        self.setStyleSheet(f"""
            QDialog#settingsDialog {{
                background: transparent;
                border: 1px solid #C4B5E0;
                border-radius: 10px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel("存储期限设置")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        root.addWidget(title)

        hint = QLabel("超过设定天数的非置顶记录将被自动清理。")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 11px;")
        root.addWidget(hint)

        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel("保留时长：")
        lbl.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 12px;")
        row.addWidget(lbl)

        self._combo = QComboBox()
        self._combo.addItems(["1 天", "3 天", "5 天"])
        days = self._settings.get("retention_days", 3)
        index_map = {1: 0, 3: 1, 5: 2}
        self._combo.setCurrentIndex(index_map.get(days, 1))
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                color: {TEXT_COLOR};
                min-width: 80px;
            }}
            QComboBox:hover {{ border-color: {TEXT_COLOR}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
        """)
        row.addWidget(self._combo)
        row.addStretch()
        root.addLayout(row)

        root.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(72, 30)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: #ffffff; border: 1px solid #d9d9d9;
                border-radius: 4px; color: {TEXT_COLOR}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {TEXT_COLOR}; }}
        """)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(72, 30)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._on_save)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TEXT_COLOR}; border: none; border-radius: 4px;
                color: #ffffff; font-size: 12px;
            }}
            QPushButton:hover {{ background: #9B85FF; }}
            QPushButton:pressed {{ background: #5B3FE0; }}
        """)
        btn_row.addWidget(ok_btn)

        root.addLayout(btn_row)

    def _on_save(self):
        days_map = {0: 1, 1: 3, 2: 5}
        self._settings["retention_days"] = days_map.get(
            self._combo.currentIndex(), 3
        )
        save_settings(self._settings)
        self.accept()
