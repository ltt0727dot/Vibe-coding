"""测试 reader.py — 使用示例 xlsx 验证解析结果"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reader import parse_xlsx

EXAMPLE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "20260410_d25-3_R4_48h.xlsx"
)


def test_parse_returns_96_wells():
    """应返回恰好 96 个孔"""
    wells = parse_xlsx(EXAMPLE_FILE)
    assert len(wells) == 96, f"Expected 96 wells, got {len(wells)}"


def test_all_positions_present():
    """所有 A1-H12 孔位应存在"""
    wells = parse_xlsx(EXAMPLE_FILE)
    rows = "ABCDEFGH"
    for r in rows:
        for c in range(1, 13):
            pos = f"{r}{c}"
            assert pos in wells, f"Missing well {pos}"


def test_spot_check_values():
    """抽查几个已知发光值"""
    wells = parse_xlsx(EXAMPLE_FILE)
    # 从上面解析的结果验证:
    # A1=66, A2=46, B1=406, H12=259
    assert wells["A1"].rlu == 66.0
    assert wells["A2"].rlu == 46.0
    assert wells["B1"].rlu == 406.0
    assert wells["H12"].rlu == 259.0


def test_well_metadata():
    """验证孔位坐标正确"""
    wells = parse_xlsx(EXAMPLE_FILE)
    assert wells["A1"].row_idx == 0
    assert wells["A1"].col_idx == 0
    assert wells["H12"].row_idx == 7
    assert wells["H12"].col_idx == 11


if __name__ == "__main__":
    test_parse_returns_96_wells()
    test_all_positions_present()
    test_spot_check_values()
    test_well_metadata()
    print("All tests passed!")
