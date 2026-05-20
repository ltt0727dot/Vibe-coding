# CLAUDE.md — History Clipboard 项目指引

## 项目简介

Windows 平台本地剪贴板历史管理软件。系统托盘运行，自动记录复制过的文字和图片，支持搜索、置顶、删除、存储期限设置。

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求规格 | [docs/requirements.md](docs/requirements.md) | 功能需求 + 非功能需求 + 范围边界 |
| 技术规范 | [docs/tech-spec.md](docs/tech-spec.md) | 技术栈、架构、数据存储、打包方案 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 色彩、字体、布局、交互规范 |
| 开发计划 | [docs/development-plan.md](docs/development-plan.md) | 分阶段任务列表及验收标准 |

## 开发日志

每天开发结束后更新 [devlog/](devlog/) 目录，文件名格式 `YYYY-MM-DD.md`，记录：
- 当日完成事项
- 待办事项
- 遇到的问题及解决方案

## 工作约定

1. **严格按阶段推进**：每阶段独立完成并验证后再进入下一阶段，不跨阶段混改代码
2. **先读文档再写代码**：每次新会话开始，先读取 docs/ 下相关规范文件，理解当前阶段目标
3. **最小改动原则**：只改当前阶段相关的文件，不做额外重构
4. **验证优先**：每个阶段完成后运行 `python src/main.py` 确认无报错
5. **devlog 同步**：每天开发结束或阶段完成时，更新 devlog 日志

## 开发阶段速览

```
阶段1 ✅ 骨架搭建   → 目录/文档/依赖/空托盘
阶段2 ✅ 数据层     → SQLite CRUD + 清理 + 验证通过
阶段3 ✅ 监听器     → 500ms轮询 + 文字/图片识别 + MD5去重
阶段4 ✅ 托盘完善   → 紫色图标 + 右键菜单(打开/设置/退出)
阶段5 ✅ 主面板 UI  → 卡片列表/搜索/置顶/删除/点击粘贴
阶段6 ✅ 设置功能   → 存储期限 1/3/5天 + 启动自动清理
阶段7 ✅ 打包 .exe  → 单文件 42MB + 运行测试通过
```

## 关键路径

```
<项目根目录>/
├── data/                  # 本地数据（不占C盘）
│   ├── clipboard.db       # SQLite 数据库
│   ├── settings.json      # 用户配置
│   └── images/            # 图片文件 + 缩略图
```

## 常用命令

```bash
# 运行程序（必须用 Python 3.11）
D:/ANACONDA/python.exe src/main.py

# 安装依赖
D:/ANACONDA/python.exe -m pip install -r requirements.txt

# 打包（阶段7）
pyinstaller --onefile --windowed --name HistoryClipboard src/main.py
```
