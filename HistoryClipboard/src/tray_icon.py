"""
系统托盘图标模块
"""
import os
import sys
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

# 图标路径：开发时 = 项目根/assets/icon.png，打包后 = PyInstaller 临时目录
if getattr(sys, "frozen", False):
    _ICON_PATH = os.path.join(sys._MEIPASS, "assets", "icon.png")
else:
    _ICON_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "icon.png"
    )


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = None
        self._settings_dialog = None

        if os.path.exists(_ICON_PATH):
            self.setIcon(QIcon(_ICON_PATH))
        else:
            self.setIcon(QIcon.fromTheme("edit-copy"))
        self.setToolTip("历史剪贴板")

        # 右键菜单
        menu = QMenu()
        open_action = QAction("打开面板", menu)
        open_action.triggered.connect(self._on_open)
        menu.addAction(open_action)

        menu.addSeparator()

        settings_action = QAction("设置", menu)
        settings_action.triggered.connect(self._on_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        # 左键点击打开面板
        self.activated.connect(self._on_activated)

    def set_main_window(self, window):
        self._main_window = window

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_open()

    def _on_open(self):
        if self._main_window:
            self._main_window.show_at_cursor()

    def _on_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        # 居中于屏幕
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.geometry().center()
            dialog.move(center.x() - dialog.width() // 2,
                        center.y() - dialog.height() // 2)
        dialog.exec()

    def _on_quit(self):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
