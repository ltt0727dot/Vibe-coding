# 编码规范

## 模块划分

每个 .py 文件职责单一：

| 文件 | 职责 |
|------|------|
| main.py | 程序入口，初始化 GUI |
| reader.py | Excel 读取，数据解析 |
| model.py | 数据类定义 |
| gui.py | 主窗口布局 |
| plate_view.py | 96 孔板 Canvas 组件 |
| label_panel.py | 右侧标注面板 |
| analysis.py | 计算逻辑 |
| charts.py | matplotlib 图表 |
| export.py | CSV/PNG 导出 |
| config.py | JSON 配置存取 |

## 命名规范

- **类**：PascalCase（如 `Well`, `PlateGrid`, `LabelPanel`）
- **函数/方法**：snake_case（如 `parse_excel()`, `compute_killing_rate()`）
- **常量**：UPPER_SNAKE_CASE（如 `DEFAULT_COLORS`, `ROW_LABELS`）
- **私有方法**：前缀 `_`（如 `_draw_grid()`, `_on_click()`）

## 注释原则

- 核心算法需有简短注释说明 WHY（不是 WHAT）
- 公共接口（类/函数签名）可用一行注释说明用途
- 不写描述代码本身的注释（如 "# 遍历列表"）

## 错误处理

- 用户可见错误 → `tkinter.messagebox`（如文件格式错误、校验失败）
- 可恢复的内部错误 → 打印 warning，不中断流程
- 致命错误 → 明确报错信息

## 导入顺序

1. 标准库
2. 第三方库
3. 项目内部模块

每组之间空一行。

## 类型提示

- 公共函数参数和返回值使用类型提示（Python 3.10+ 语法）
- 示例：`def parse_excel(path: str) -> dict[str, Well]:`
