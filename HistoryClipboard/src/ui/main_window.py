"""
主面板窗口 — 剪贴板历史卡片列表 + 搜索 + 操作
紫色主题，淡紫半透明背景（paintEvent 手绘，兼容 Windows）
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QScrollArea, QPushButton,
                                QApplication, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen

from database import (get_items, delete_item, toggle_pin, get_total_count)
from ui.card_widget import ClipboardCard

# ---- 紫色调色板 ----
PURPLE = "#7B61FF"
PURPLE_LIGHT = "#A78BFA"
PURPLE_HOVER = "#8B6FE0"
PURPLE_BORDER = "#C4B5E0"
BG_R, BG_G, BG_B = 184, 137, 219  # #B889DB
BG_ALPHA = 115                      # 0.45 * 255 ≈ 115 (55%透明)


class MainWindow(QWidget):
    """剪贴板历史面板"""

    item_copied = Signal(dict)  # 用户从面板复制内容后发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._search_text = ""

        self.setWindowTitle("历史剪贴板")
        self.setFixedSize(380, 520)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(self._base_style())

        self._setup_ui()
        self._load_data()

        # 搜索防抖
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._load_data)

    # ---------- 样式 ----------

    def _base_style(self):
        return f"""
            QWidget#mainPanel {{
                background: transparent;
                border: 1px solid {PURPLE_BORDER};
                border-radius: 12px;
            }}
        """

    # ---------- UI 搭建 ----------

    def _setup_ui(self):
        self.setObjectName("mainPanel")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 标题栏 ----
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(16, 10, 12, 10)

        title_lbl = QLabel("History Clipboard")
        title_lbl.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #612A8A;")
        title_bar.addWidget(title_lbl)
        title_bar.addStretch()

        # 最小化按钮（点击后隐藏到托盘）
        min_btn = QPushButton("─")
        min_btn.setFixedSize(28, 28)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setToolTip("最小化到托盘")
        min_btn.clicked.connect(self.hide)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                border: none; background: transparent;
                color: #612A8A; font-size: 16px; border-radius: 6px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: #e0d0f0; color: {PURPLE};
            }}
        """)
        title_bar.addWidget(min_btn)
        root.addLayout(title_bar)

        # ---- 搜索栏 ----
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 0, 12, 8)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索...")
        self._search_input.setFixedHeight(34)
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background: #ffffff;
                border: 1px solid {PURPLE_BORDER};
                border-radius: 17px;
                padding: 0 14px;
                font-size: 12px;
                color: #1f1f1f;
            }}
            QLineEdit:focus {{
                border-color: {PURPLE};
            }}
        """)
        search_layout.addWidget(self._search_input)
        root.addLayout(search_layout)

        # ---- 卡片列表滚动区 ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 4px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #d0c8e0; border-radius: 2px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        self._card_container = QWidget()
        self._card_container.setObjectName("cardContainer")
        self._card_container.setStyleSheet("background: transparent;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 4, 0, 8)
        self._card_layout.setSpacing(2)
        self._card_layout.addStretch()

        scroll.setWidget(self._card_container)
        root.addWidget(scroll)

        # ---- 底部状态栏 ----
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 6, 16, 8)
        self._count_label = QLabel()
        self._count_label.setStyleSheet(f"color: {PURPLE_LIGHT}; font-size: 11px;")
        footer.addWidget(self._count_label)
        root.addLayout(footer)

    # ---------- 数据加载 ----------

    def _load_data(self):
        """从数据库重新加载卡片"""
        for i in reversed(range(self._card_layout.count())):
            widget = self._card_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        self._items = get_items(search=self._search_text or None)

        pinned_ids = set()
        for item in self._items:
            card = ClipboardCard(item)
            card.clicked.connect(self._on_item_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.delete_requested.connect(self._on_delete_requested)
            self._card_layout.addWidget(card)
            if item.get("pinned"):
                pinned_ids.add(item["id"])

        if pinned_ids and len(pinned_ids) < len(self._items):
            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setStyleSheet(
                f"QFrame {{ color: {PURPLE_BORDER}; margin: 6px 16px; max-height: 1px; }}"
            )
            idx = len(pinned_ids)
            self._card_layout.insertWidget(idx, divider)

        self._card_layout.addStretch()

        total = get_total_count()
        self._count_label.setText(f"共 {total} 条记录"
                                  + (f"，显示 {len(self._items)} 条" if self._search_text else ""))

    def refresh(self):
        self._load_data()

    # ---------- 交互逻辑 ----------

    def _on_item_clicked(self, item: dict):
        """点击卡片 → 复制到剪贴板（发信号让监听器跳过此内容）"""
        self.item_copied.emit(item)

        clipboard = QApplication.clipboard()
        if item["type"] == "text":
            clipboard.setText(item["content"])
        elif item["type"] == "image":
            pixmap = QPixmap(item["image_path"])
            if not pixmap.isNull():
                clipboard.setPixmap(pixmap)

    def _on_pin_toggled(self, item_id: int):
        toggle_pin(item_id)
        self._load_data()

    def _on_delete_requested(self, item_id: int):
        info = delete_item(item_id)
        if info and info.get("image_path"):
            import os
            for p in (info["image_path"], info.get("thumbnail_path", "")):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        self._load_data()

    def _on_search_changed(self, text: str):
        self._search_text = text
        self._search_timer.stop()
        self._search_timer.start(150)

    # ---------- 窗口行为 ----------

    def paintEvent(self, event):
        """手绘半透明紫色背景，解决 Windows 下 stylesheet rgba 不生效问题"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(BG_R, BG_G, BG_B, BG_ALPHA))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    def show_at_cursor(self):
        """在屏幕右下角显示面板"""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.width() - 12
            y = geo.bottom() - self.height() - 12
            self.move(x, y)
        self._load_data()
        self._search_input.clear()
        self._search_input.setFocus()
        self.show()
        self.activateWindow()
