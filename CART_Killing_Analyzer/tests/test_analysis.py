"""测试 analysis.py"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model import Well
from analysis import compute_killing, sort_groups_by_et


def _make_well(pos, rlu, cell_type="", et="", tumor=False):
    return Well(position=pos, row_idx=0, col_idx=0, rlu=rlu,
                cell_type=cell_type, et_ratio=et, is_tumor_only=tumor)


def test_raises_without_tumor_only():
    wells = {"A1": _make_well("A1", 100, "Control", "1:1")}
    try:
        compute_killing(wells)
        assert False, "Should have raised"
    except ValueError as e:
        assert "tumor-only" in str(e)


def test_killing_formula():
    """验证杀伤率公式: Killing = (1 - RLU / T_only_mean) * 100"""
    wells = {
        "A1": _make_well("A1", 200, cell_type="KO", et="1:1"),
        "B1": _make_well("B1", 100, cell_type="KO", et="1:1"),
        "C1": _make_well("C1", 300, tumor=True),
    }
    results, t_mean, stats = compute_killing(wells)
    assert t_mean == 300.0
    # A1: (1 - 200/300) * 100 = 33.33
    # B1: (1 - 100/300) * 100 = 66.67
    a1 = [r for r in results if r.position == "A1"][0]
    b1 = [r for r in results if r.position == "B1"][0]
    c1 = [r for r in results if r.position == "C1"][0]
    assert round(a1.killing_pct, 2) == 33.33
    assert round(b1.killing_pct, 2) == 66.67
    assert round(c1.killing_pct, 2) == 0.00  # tumor-only itself


def test_group_stats():
    """测试分组统计：均值、标准差"""
    wells = {
        "A1": _make_well("A1", 200, "KO", "1:1"),
        "A2": _make_well("A2", 100, "KO", "1:1"),
        "B1": _make_well("B1", 150, "KO", "5:1"),
        "C1": _make_well("C1", 300, tumor=True),
    }
    results, t_mean, stats = compute_killing(wells)

    group_1_1 = [s for s in stats if s.et_ratio == "1:1"][0]
    assert group_1_1.count == 2
    assert group_1_1.sd_killing is not None

    group_5_1 = [s for s in stats if s.et_ratio == "5:1"][0]
    assert group_5_1.count == 1
    assert group_5_1.sd_killing is None


def test_sort_groups_by_et():
    from model import GroupStats
    groups = [
        GroupStats("KO", "5:1", 3, 50.0, 5.0),
        GroupStats("KO", "0:1", 3, 10.0, 2.0),
        GroupStats("KO", "1:1", 3, 30.0, 3.0),
    ]
    sorted_groups = sort_groups_by_et(groups)
    assert sorted_groups[0].et_ratio == "0:1"
    assert sorted_groups[1].et_ratio == "1:1"
    assert sorted_groups[2].et_ratio == "5:1"


if __name__ == "__main__":
    test_raises_without_tumor_only()
    test_killing_formula()
    test_group_stats()
    test_sort_groups_by_et()
    print("All analysis tests passed!")
