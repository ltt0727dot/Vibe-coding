"""
History Clipboard - Windows 剪贴板历史管理工具
入口模块：初始化应用、启动托盘、启动剪贴板监听
"""
import sys
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HistoryClipboard")
    app.setQuitOnLastWindowClosed(False)

    # 初始化数据库（数据存储在项目本地 data/ 目录）
    from database import init_db, cleanup_expired
    init_db()

    # 根据用户设置清理过期记录
    from utils import load_settings
    settings = load_settings()
    cleanup_expired(settings.get("retention_days", 3))

    # 启动剪贴板监听
    from clipboard_monitor import ClipboardMonitor
    monitor = ClipboardMonitor(app)

    # 创建主面板
    from ui.main_window import MainWindow
    window = MainWindow()

    # 监听器发现新内容 → 自动刷新面板
    monitor.new_item_added.connect(lambda _: window.refresh())

    # 面板复制内容 → 通知监听器跳过一个轮询周期，防止重复记录
    window.item_copied.connect(lambda _: monitor.skip_next_poll())

    # 托盘图标
    from tray_icon import TrayIcon
    tray = TrayIcon()
    tray.set_main_window(window)
    tray.show()

    # 首次启动（无历史记录）自动弹出面板，让用户知道程序在运行
    from database import get_total_count
    if get_total_count() == 0:
        window.show_at_cursor()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
