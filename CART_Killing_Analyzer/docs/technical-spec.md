# 技术规范

## 技术栈

| 组件 | 选型 | 版本要求 |
|------|------|----------|
| 语言 | Python | 3.7+ |
| GUI | Tkinter | 内置 |
| 绘图 | matplotlib | 3.5+ |
| 数据处理 | pandas | 1.3+ |
| Excel 读取 | stdlib (zipfile + xml) | 内置 |
| 打包 | PyInstaller | 5.0+ |

## 架构分层

```
GUI 层 (gui.py)       ← Tkinter 主窗口 + plate_view + label_panel + charts
分析引擎 (analysis)     ← 杀伤率计算 + 分组统计
数据层 (reader + model) ← Excel 解析 + Well 数据结构
```

## 数据流

```
Excel 文件 → reader.parse() → dict[str, Well]
                                   │
               ┌───────────────────┴────────────────┐
               ▼                                    ▼
      label_panel 交互标注                 analysis.compute()
               │                                    │
               ▼                                    ▼
      config.save/load()                charts.render() + export.csv()
```

## 96 孔板坐标体系

- 行：A(0) B(1) C(2) D(3) E(4) F(5) G(6) H(7)
- 列：1(0) 2(1) 3(2) ... 12(11)
- 孔位 ID："{row_letter}{col_number}"，如 "A1", "H12"

## E:T 比例排序规则

- 解析字符串如 "5:1" → 计算数值 = 5/1 = 5
- 解析 "1:5" → 数值 = 1/5 = 0.2
- 解析 "0:1" → 数值 = 0/1 = 0（无效应细胞）
- X 轴按此数值升序排列

## 杀伤率公式

```
T_only_mean = Σ(RLU of tumor-only wells) / N_tumor_only
Killing_i(%) = (1 - RLU_i / T_only_mean) × 100
```

- RLU_i 越低 → 杀伤越强 → Killing% 越高
- 可能为负值（RLU > T_only_mean），不截断

## 分组统计

- 分组键：(cell_type, et_ratio)
- 排除 is_tumor_only=True 的孔
- 组内 N≥2 → mean ± sd（误差棒）
- 组内 N=1 → mean=杀伤率, sd=None（不画误差棒）
