# 开发阶段计划

## 总体原则
- 每阶段独立可验证，完成后再进入下一阶段
- 不跨阶段修改代码
- 每阶段完成后更新 devlog

---

## 阶段 1：项目骨架搭建 ✅
**目标**：目录就绪，文档齐全，程序能启动显示托盘图标

- [x] 创建目录结构
- [x] 创建 docs/ 四份规范文件
- [x] 创建 devlog/ 首日日志
- [x] 创建 requirements.txt
- [x] 创建 main.py（QApplication + 空托盘图标）
- [x] 创建 CLAUDE.md

---

## 阶段 2：数据层 ✅
**目标**：SQLite 数据库就绪，增删查改功能可用

- [x] 实现 database.py：建表、增、删、查、置顶、过期清理
- [x] 编写验证脚本确认 CRUD 正确（10/10 通过）

---

## 阶段 3：剪贴板监听 ✅
**目标**：后台自动记录复制内容

- [x] 实现 clipboard_monitor.py（QTimer 500ms 轮询）
- [x] 文字复制记录验证
- [x] 图片复制记录验证
- [x] 去重逻辑验证
- [x] offscreen 模式启动无报错

---

## 阶段 4：系统托盘 ✅
**目标**：托盘图标功能完整

- [x] 实现托盘图标 + 右键菜单
- [x] 左键弹出面板
- [x] 菜单项：打开 / 设置 / 退出
- [x] 紫色剪贴板图标（assets/icon.png）
- [x] 数据存储迁移到项目本地 data/

---

## 阶段 5：主面板 UI ✅
**目标**：核心交互界面完成

- [x] 实现 main_window.py + card_widget.py
- [x] 卡片列表（时间倒序 + 置顶优先 + 分割线）
- [x] 搜索栏实时过滤（150ms 防抖）
- [x] 点击复制回剪贴板 + 面板自动隐藏
- [x] 置顶/删除操作（含图片文件清理）
- [x] 屏幕右下角弹出定位
- [x] 失焦自动隐藏
- [x] 4项功能测试全部通过

---

## 阶段 6：设置功能 ✅
**目标**：存储期限可配置

- [x] 实现 settings_dialog.py
- [x] 配置文件读写（utils.py load/save_settings）
- [x] 过期清理对接（启动时自动执行）
- [x] 4项测试全部通过

---

## 阶段 7：打包与收尾 ✅
**目标**：交付可用 .exe

- [x] PyInstaller 打包（--onefile --windowed）
- [x] sqlite3.dll 依赖解决
- [x] 图标嵌入（--add-data + sys._MEIPASS）
- [x] offscreen 模式验证通过
- [x] exe 可分享给其他 Windows 用户直接运行

## 构建命令

```bash
# 创建 venv 并安装依赖
D:/ANACONDA/python.exe -m venv build_env
build_env/Scripts/python.exe -m pip install PySide6==6.5.3 pyinstaller

# 打包
build_env/Scripts/python.exe -m PyInstaller \
    --onefile --windowed \
    --name HistoryClipboard \
    --add-data "assets/icon.png;assets" \
    --add-binary "d:/anaconda/Library/bin/sqlite3.dll;." \
    src/main.py

# 输出: dist/HistoryClipboard.exe
```

## 最终交付物

- `dist/HistoryClipboard.exe` — 单个 exe 文件（42MB）
- 发给其他 Windows 用户，双击即运行
- 运行后在 exe 同目录自动创建 `data/` 存放数据
