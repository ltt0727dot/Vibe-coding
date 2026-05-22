# CLAUDE.md — CAR-T 杀伤分析工具

## 项目简介

Windows .exe 桌面工具，用于 CAR-T 杀伤实验数据分析：读取酶标仪 96 孔板 RLU 数据，交互标注细胞类型/E:T，计算杀伤率并生成图表。

## 标准文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求规格 | [docs/requirements.md](docs/requirements.md) | 功能需求（FR-001 ~ FR-010） |
| 技术规范 | [docs/technical-spec.md](docs/technical-spec.md) | 技术栈、架构、数据流、公式 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 布局、配色、字体、交互 |
| 开发计划 | [docs/development-plan.md](docs/development-plan.md) | 9 阶段任务清单 |
| 编码规范 | [docs/coding-standards.md](docs/coding-standards.md) | 模块命名、注释、错误处理 |
| 开发日志 | [devlogs/](devlogs/) | 每日进展记录 |

## 工作流程

1. **读 devlog** — 先看 [devlogs/](devlogs/) 中最新的日志，了解当前进度
2. **读相关 docs** — 根据当前阶段参考 [docs/](docs/) 中的规范
3. **执行任务** — 按 [docs/development-plan.md](docs/development-plan.md) 的阶段顺序推进
4. **更新 devlog** — 每完成一个子任务，写入当天日志
5. **验证** — 每阶段完成后按验证标准确认

## 项目结构

```
Killingassay/
├── CLAUDE.md              ← 本文件
├── README.md              ← 用户写的原始需求
├── requirements.txt
├── docs/                  ← 规范文档
├── devlogs/               ← 每日开发日志
├── src/                   ← 源代码
│   ├── main.py            # 入口
│   ├── reader.py          # Excel 解析
│   ├── model.py           # 数据模型
│   ├── gui.py             # 主布局
│   ├── plate_view.py      # 96 孔板组件
│   ├── label_panel.py     # 标注面板
│   ├── analysis.py        # 计算引擎
│   ├── charts.py          # 图表
│   ├── export.py          # 导出
│   └── config.py          # 配置存取
├── tests/                 ← 测试
└── build/                 ← 打包
```

## 开发原则

- **一次只推进一个阶段**，完成 → 验证 → 再进入下一阶段
- **不跨阶段开发**，基础没搭好前不做上层功能
- **始终用示例 xlsx** (`20260410_d25-3_R4_48h.xlsx`) 作为测试输入
- **小步提交**，每次改动后确保之前验证通过的功能不回归

## 技术栈速查

- GUI: Tkinter（内置）
- 绘图: matplotlib + FigureCanvasTkAgg
- 数据: pandas + openpyxl
- 打包: PyInstaller
- 目标: Python 3.10+，Windows .exe 单文件
