"""matplotlib 图表生成"""

import tkinter as tk
from typing import Dict, List, Optional
from collections import defaultdict

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from model import GroupStats
from analysis import sort_groups_by_et

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
matplotlib.rcParams["axes.unicode_minus"] = False

DEFAULT_COLORS = {
    "AAVS1_KO": "#EF4444",
    "Target gene_KO": "#F59E0B",
}
FALLBACK_PALETTE = [
    "#2563EB", "#DC2626", "#16A34A", "#9333EA",
    "#EA580C", "#0891B2", "#D946EF", "#65A30D",
]


def get_default_color(cell_type: str, index: int = 0) -> str:
    if cell_type in DEFAULT_COLORS:
        return DEFAULT_COLORS[cell_type]
    return FALLBACK_PALETTE[index % len(FALLBACK_PALETTE)]


def create_main_chart(
    parent: tk.Widget,
    stats: List[GroupStats],
    title: str = "CAR-T 杀伤曲线",
    xlabel: str = "E:T",
    ylabel: str = "% of Cytolysis",
    color_map: Dict[str, str] = None,
):
    """主图：所有细胞类型对比"""
    by_type: Dict[str, List[GroupStats]] = defaultdict(list)
    for gs in sort_groups_by_et(stats):
        by_type[gs.cell_type].append(gs)

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    cm = color_map or {}

    for idx, (ct, groups) in enumerate(by_type.items()):
        groups = sort_groups_by_et(groups)
        x_labels = [g.et_ratio for g in groups]
        x_pos = list(range(len(groups)))
        y_vals = [g.mean_killing for g in groups]
        y_errs = [g.sd_killing if g.sd_killing else 0 for g in groups]
        color = cm.get(ct, get_default_color(ct, idx))

        ax.errorbar(
            x_pos, y_vals, yerr=y_errs,
            marker="o", color=color, label=ct,
            capsize=4, linewidth=1.5, markersize=6,
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas, fig


def create_compare_chart(
    parent: tk.Widget,
    stats: List[GroupStats],
    type1: str,
    type2: str,
    title: str = "",
    xlabel: str = "E:T",
    ylabel: str = "% of Cytolysis",
    color_map: Dict[str, str] = None,
    post_hoc: Dict[str, dict] = None,
):
    """对比图：两种细胞类型 + 显著性星标"""
    all_groups = sort_groups_by_et(stats)
    cm = color_map or {}

    fig = Figure(figsize=(6, 3.5), dpi=100)
    ax = fig.add_subplot(111)

    x_labels_all = []
    for idx, ct in enumerate([type1, type2]):
        groups = [g for g in all_groups if g.cell_type == ct]
        groups = sort_groups_by_et(groups)
        if not groups:
            continue
        x_labels = [g.et_ratio for g in groups]
        if not x_labels_all:
            x_labels_all = x_labels
        x_pos = list(range(len(groups)))
        y_vals = [g.mean_killing for g in groups]
        y_errs = [g.sd_killing if g.sd_killing else 0 for g in groups]
        color = cm.get(ct, get_default_color(ct, idx))

        ax.errorbar(
            x_pos, y_vals, yerr=y_errs,
            marker="o", color=color, label=ct,
            capsize=4, linewidth=1.5, markersize=6,
        )

    # 显著性星标
    if post_hoc and x_labels_all:
        for j, et in enumerate(x_labels_all):
            if et in post_hoc and post_hoc[et]["stars"]:
                stars = post_hoc[et]["stars"]
                g1 = [g.mean_killing for g in all_groups if g.cell_type == type1 and g.et_ratio == et]
                g2 = [g.mean_killing for g in all_groups if g.cell_type == type2 and g.et_ratio == et]
                if g1 and g2:
                    y_max = max(g1[0], g2[0])
                    is_sig = stars != "ns"
                    ax.annotate(
                        stars, (j, y_max),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha="center",
                        fontsize=11 if is_sig else 9,
                        fontweight="bold" if is_sig else "normal",
                        color="#1A365D" if is_sig else "#94A3B8",
                    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title or f"{type1} vs {type2}")
    ax.set_xticks(range(len(x_labels_all)))
    ax.set_xticklabels(x_labels_all)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas, fig
