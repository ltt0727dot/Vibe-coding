"""导出为 xlsx（三 sheet）+ PNG"""

import os
import csv
from typing import Dict, List
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from model import Well, WellResult, GroupStats
from analysis import sort_groups_by_et, anova_two_way, _et_numeric


HEADER_FONT = Font(name="Microsoft YaHei", bold=True, size=10)
DATA_FONT = Font(name="Microsoft YaHei", size=10)
HEADER_FILL = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)


def _style_header(ws, row, col_count):
    for c in range(1, col_count + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = Alignment(horizontal="center")


def export_results_xlsx(
    results: List[WellResult],
    wells: Dict[str, Well],
    group_stats: List[GroupStats],
    t_only_mean: float,
    output_path: str,
    compare_type1: str = "",
    compare_type2: str = "",
    anova_result: dict = None,
    post_hoc: dict = None,
):
    """导出完整分析结果为 xlsx 文件

    Sheet 1: 详细数据（每孔一行）
    Sheet 2: % of Cytolysis（Prism 兼容宽格式）
    Sheet 3: Two-way ANOVA（仅在用户做了对比时）
    """
    wb = Workbook()

    # === Sheet 1: 详细数据 ===
    ws1 = wb.active
    ws1.title = "详细数据"
    headers1 = [
        "孔位置", "细胞类型", "E:T 比例", "原始发光值 (RLU)",
        "全局分母 (T_only_mean)", "杀伤率 (%)", "组内均值 (%)", "组内标准差 (%)",
    ]
    ws1.append(headers1)
    _style_header(ws1, 1, len(headers1))

    sorted_results = sorted(results, key=lambda r: (r.position[0], int(r.position[1:])))
    for wr in sorted_results:
        ws1.append([
            wr.position,
            wr.cell_type,
            wr.et_ratio,
            wr.rlu,
            round(t_only_mean, 1),
            wr.killing_pct,
            wr.group_mean if wr.group_mean else "",
            wr.group_sd if wr.group_sd else "",
        ])
        row = ws1.max_row
        for c in range(1, len(headers1) + 1):
            cell = ws1.cell(row=row, column=c)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center")
            # E:T 列设置为文本格式
            if c == 3:
                cell.number_format = "@"

    # 自动列宽
    for c in range(1, len(headers1) + 1):
        ws1.column_dimensions[get_column_letter(c)].width = 16

    # === Sheet 2: % of Cytolysis (Prism 格式) ===
    ws2 = wb.create_sheet("% of Cytolysis")

    # 按细胞类型 + E:T 分组收集个体杀伤值
    by_type_et: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for wr in sorted_results:
        well = wells.get(wr.position)
        if not well or well.is_tumor_only or not well.cell_type:
            continue
        if wr.et_ratio:
            by_type_et[wr.cell_type][wr.et_ratio].append(wr.killing_pct)

    cell_types = list(by_type_et.keys())
    et_ratios = sorted(
        {et for ct_data in by_type_et.values() for et in ct_data},
        key=_et_numeric,
    )

    if cell_types and et_ratios:
        max_reps = max(
            len(vals) for ct_data in by_type_et.values() for vals in ct_data.values()
        )

        # Row 1: Header "% of Cytolysis"
        ws2.merge_cells(
            start_row=1, start_column=1, end_row=1, end_column=1 + len(cell_types) * max_reps
        )
        ws2.cell(row=1, column=1, value="% of Cytolysis").font = Font(
            name="Microsoft YaHei", bold=True, size=12,
        )

        # Row 2: 细胞类型标题
        for ct_idx, ct in enumerate(cell_types):
            start_c = 2 + ct_idx * max_reps
            end_c = 1 + (ct_idx + 1) * max_reps
            if end_c > start_c:
                ws2.merge_cells(start_row=2, start_column=start_c, end_row=2, end_column=end_c)
            ws2.cell(row=2, column=start_c, value=ct).font = HEADER_FONT

        # Data rows
        for et_idx, et in enumerate(et_ratios):
            row = 3 + et_idx
            ws2.cell(row=row, column=1, value=et).font = DATA_FONT
            ws2.cell(row=row, column=1).number_format = "@"  # E:T 文本格式
            for ct_idx, ct in enumerate(cell_types):
                vals = by_type_et[ct].get(et, [])
                for rep_idx in range(max_reps):
                    col = 2 + ct_idx * max_reps + rep_idx
                    if rep_idx < len(vals):
                        cell = ws2.cell(row=row, column=col, value=round(vals[rep_idx], 4))
                    cell.font = DATA_FONT
                    cell.alignment = Alignment(horizontal="center")

    # === Sheet 3: Two-way ANOVA（可选） ===
    if anova_result and compare_type1 and compare_type2:
        ws3 = wb.create_sheet("Two-way ANOVA")

        ws3.merge_cells("A1:D1")
        ws3.cell(row=1, column=1, value=f"Two-way ANOVA: {compare_type1} vs {compare_type2}").font = Font(
            name="Microsoft YaHei", bold=True, size=12,
        )

        # ANOVA 表
        anova_table, anova_stats = anova_result
        if not anova_table.empty:
            ws3.cell(row=3, column=1, value="Two-way ANOVA 结果").font = HEADER_FONT
            headers = ["变异来源", "df", "F", "p", "显著性"]
            for c, h in enumerate(headers, 1):
                ws3.cell(row=4, column=c, value=h).font = HEADER_FONT

            for i, factor in enumerate(anova_table.index):
                r = 5 + i
                ws3.cell(row=r, column=1, value=factor).font = DATA_FONT
                ws3.cell(row=r, column=2, value=round(anova_table.loc[factor, "df"], 3)).font = DATA_FONT
                ws3.cell(row=r, column=3, value=round(anova_table.loc[factor, "F"], 3)).font = DATA_FONT
                ws3.cell(row=r, column=4, value=round(anova_table.loc[factor, "PR(>F)"], 5)).font = DATA_FONT
                stars = anova_stats.get(factor, {}).get("stars", "")
                ws3.cell(row=r, column=5, value=stars).font = DATA_FONT

        # 事后检验表
        if post_hoc:
            start_row = ws3.max_row + 3
            ws3.cell(row=start_row, column=1, value="事后检验（各 E:T 水平）").font = HEADER_FONT
            ph_headers = ["E:T 比例", "t 统计量", "p 值", "显著性"]
            for c, h in enumerate(ph_headers, 1):
                ws3.cell(row=start_row + 1, column=c, value=h).font = HEADER_FONT

            for i, (et, info) in enumerate(post_hoc.items()):
                r = start_row + 2 + i
                ws3.cell(row=r, column=1, value=et).font = DATA_FONT
                ws3.cell(row=r, column=1).number_format = "@"
                ws3.cell(row=r, column=2, value=str(info["t_stat"])).font = DATA_FONT
                ws3.cell(row=r, column=3, value=str(info["p"])).font = DATA_FONT
                ws3.cell(row=r, column=4, value=info["stars"]).font = DATA_FONT

    wb.save(output_path)


def export_full_csv(results: List[WellResult], t_only_mean: float, filepath: str):
    """导出完整数据 CSV（保留向后兼容）"""
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "孔位置", "细胞类型", "E:T 比例", "原始发光值 (RLU)",
            "全局分母 (T_only_mean)", "杀伤率 (%)",
            "组内均值 (%)", "组内标准差 (%)",
        ])
        for r in sorted(results, key=lambda x: (x.position[0], int(x.position[1:]))):
            writer.writerow([
                r.position, r.cell_type, r.et_ratio, r.rlu,
                round(t_only_mean, 1),
                r.killing_pct,
                r.group_mean if r.group_mean else "",
                r.group_sd if r.group_sd else "",
            ])


def export_wide_csv(stats: List[GroupStats], filepath: str):
    """导出宽格式 CSV"""
    sorted_groups = sort_groups_by_et(stats)
    et_ratios = list(dict.fromkeys(g.et_ratio for g in sorted_groups))
    cell_types = list(dict.fromkeys(g.cell_type for g in sorted_groups))

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["细胞类型 \\ E:T"] + et_ratios)
        for ct in cell_types:
            row = [ct]
            for et in et_ratios:
                match = [g for g in sorted_groups if g.cell_type == ct and g.et_ratio == et]
                row.append(match[0].mean_killing if match else "")
            writer.writerow(row)


def save_figure(fig, default_name: str = "chart.png"):
    """保存 matplotlib figure 为 PNG"""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.asksaveasfilename(
        title="保存图表为 PNG",
        defaultextension=".png",
        filetypes=[("PNG 图片", "*.png")],
        initialfile=default_name,
    )
    root.destroy()
    if filepath:
        fig.savefig(filepath, dpi=150, bbox_inches="tight")
        return filepath
    return None
