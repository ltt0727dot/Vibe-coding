"""杀伤率计算、分组统计、Two-way ANOVA"""

import statistics
from typing import Dict, List, Optional, Tuple

import pandas as pd
import scipy.stats as scistats
import statsmodels.api as sm
from statsmodels.formula.api import ols

from model import Well, GroupStats, WellResult


def _et_numeric(et_str: str) -> float:
    """将 E:T 字符串转为数值"""
    parts = et_str.split(":")
    if len(parts) != 2:
        return float("inf")
    try:
        return float(parts[0]) / float(parts[1])
    except (ValueError, ZeroDivisionError):
        return float("inf")


def compute_killing(wells: Dict[str, Well]) -> Tuple[List[WellResult], float, List[GroupStats]]:
    """执行完整分析计算，返回 (结果列表, T_only_mean, 分组统计列表)

    Raises:
        ValueError: 若没有 tumor-only 孔
    """
    # 收集 tumor-only 孔
    tumor_wells = [w for w in wells.values() if w.is_tumor_only]
    if not tumor_wells:
        raise ValueError("请至少标记一个 tumor-only 孔作为归一化分母")

    t_only_mean = sum(w.rlu for w in tumor_wells) / len(tumor_wells)

    # 计算每个孔的杀伤率
    well_results: List[WellResult] = []
    for w in wells.values():
        killing = (1 - w.rlu / t_only_mean) * 100
        well_results.append(WellResult(
            position=w.position,
            cell_type=w.cell_type,
            et_ratio=w.et_ratio,
            rlu=w.rlu,
            t_only_mean=t_only_mean,
            killing_pct=round(killing, 4),
            group_mean=0.0,  # 下面填充
            group_sd=None,
        ))

    # 分组统计（排除 tumor-only 和未标注孔）
    groups: Dict[Tuple[str, str], List[WellResult]] = {}
    for wr in well_results:
        well = wells[wr.position]
        if well.is_tumor_only or not well.cell_type:
            continue
        key = (wr.cell_type, wr.et_ratio)
        groups.setdefault(key, []).append(wr)

    group_stats: List[GroupStats] = []
    for (ct, et), members in groups.items():
        killing_vals = [m.killing_pct for m in members]
        mean_val = statistics.mean(killing_vals)
        sd_val = statistics.stdev(killing_vals) if len(members) >= 2 else None

        # 填充每个成员的分组信息
        for m in members:
            m.group_mean = round(mean_val, 4)
            m.group_sd = round(sd_val, 4) if sd_val is not None else None

        group_stats.append(GroupStats(
            cell_type=ct,
            et_ratio=et,
            count=len(members),
            mean_killing=round(mean_val, 4),
            sd_killing=round(sd_val, 4) if sd_val is not None else None,
        ))

    return well_results, t_only_mean, group_stats


def sort_groups_by_et(stats: List[GroupStats]) -> List[GroupStats]:
    """按 E:T 比例数值排序分组"""
    return sorted(stats, key=lambda gs: _et_numeric(gs.et_ratio))


def anova_two_way(
    results: List[WellResult], type1: str, type2: str
) -> Tuple[pd.DataFrame, dict, dict]:
    """Two-way ANOVA + 每 E:T 水平的事后检验

    Args:
        results: 全部 WellResult
        type1, type2: 要比较的两种细胞类型

    Returns:
        (anova_table, anova_stats, post_hoc_results)
        anova_table: statsmodels ANOVA 表
        anova_stats: {factor: {F, p, significant}}
        post_hoc_results: {et_ratio: {t_stat, p, stars}}
    """
    # 筛选两种细胞类型的数据
    df = pd.DataFrame([
        {"cell_type": r.cell_type, "et_ratio": r.et_ratio, "killing": r.killing_pct}
        for r in results
        if r.cell_type in (type1, type2) and r.et_ratio
    ])

    if df.empty or df["cell_type"].nunique() < 2 or df["et_ratio"].nunique() < 2:
        return pd.DataFrame(), {}, {}

    # Two-way ANOVA
    model = ols("killing ~ C(cell_type) + C(et_ratio) + C(cell_type):C(et_ratio)", data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)

    anova_stats = {}
    for factor in anova_table.index:
        row = anova_table.loc[factor]
        p = row["PR(>F)"]
        if p < 0.001:
            stars = "***"
        elif p < 0.01:
            stars = "**"
        elif p < 0.05:
            stars = "*"
        else:
            stars = "ns"
        anova_stats[factor] = {
            "F": round(row["F"], 3),
            "p": round(p, 5),
            "significant": p < 0.05,
            "stars": stars,
        }

    # 事后检验：每个 E:T 水平下两种细胞类型的 t 检验
    post_hoc = {}
    et_levels = sorted(df["et_ratio"].unique(), key=_et_numeric)
    for et in et_levels:
        g1 = df[(df["cell_type"] == type1) & (df["et_ratio"] == et)]["killing"]
        g2 = df[(df["cell_type"] == type2) & (df["et_ratio"] == et)]["killing"]
        if len(g1) < 1 or len(g2) < 1:
            continue
        if len(g1) >= 2 and len(g2) >= 2:
            t_stat, p_val = scistats.ttest_ind(g1, g2)
        else:
            t_stat, p_val = float("nan"), float("nan")
        if p_val < 0.001:
            stars = "***"
        elif p_val < 0.01:
            stars = "**"
        elif p_val < 0.05:
            stars = "*"
        else:
            stars = "ns"
        post_hoc[et] = {
            "t_stat": round(t_stat, 3) if not pd.isna(t_stat) else "N/A (n<2)",
            "p": round(p_val, 5) if not pd.isna(p_val) else "N/A (n<2)",
            "stars": stars,
        }

    return anova_table, anova_stats, post_hoc
