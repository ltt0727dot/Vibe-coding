# 技术规范文档

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11+ |
| UI 框架 | PySide6 | 6.6+ |
| 数据库 | SQLite | 3 (内置) |
| 打包工具 | PyInstaller | 6.x |

## 项目依赖 (`requirements.txt`)

```
PySide6>=6.6.0
Pillow>=10.0.0
```

## 架构说明

采用**单进程多线程**架构：

```
main.py (主线程)
  ├── 初始化 QApplication
  ├── 启动 ClipboardMonitor (后台线程)
  ├── 创建 TrayIcon (UI 线程)
  └── 进入事件循环
```

- **主线程**：Qt 事件循环，处理 UI
- **ClipboardMonitor 线程**：轮询剪贴板变化，写入数据库
- 线程间通过 Qt Signal/Slot 通信

## 数据存储

所有数据存储在**项目本地 `data/` 目录**，不占用系统盘。

### 数据库文件
- 路径：`<项目根>/data/clipboard.db`
- 引擎：SQLite，WAL 模式

### 图片文件
- 路径：`<项目根>/data/images/`
- 命名：`{timestamp}_{uuid}.png`
- 缩略图：同目录 `{timestamp}_{uuid}_thumb.png`，尺寸 60×60

### 配置文件
- 路径：`<项目根>/data/settings.json`
- 内容：`{ "retention_days": 3 }`

## 剪贴板监听策略

- 使用 `QApplication.clipboard().dataChanged` 信号（Qt 原生方式）
- 备用方案：500ms 定时轮询 `QClipboard.mimeData()`
- 去重：比对 hash（文字用 md5，图片用文件 md5）

## 打包配置

- PyInstaller 单文件模式 (`--onefile`)
- 包含资源：托盘图标、Qt 平台插件
- 输出：`dist/HistoryClipboard.exe`
- 图标嵌入 exe

## 注意事项

1. Windows 剪贴板在程序退出后仍保留内容，不会丢失
2. 图片保存为 PNG 格式以保持质量
3. 数据库连接使用线程锁保护
4. 窗口关闭 = 隐藏到托盘，不是退出
