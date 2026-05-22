"""测试 config.py"""

import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model import Well
from config import (
    wells_to_config, config_to_labels, save_config, load_config, apply_config,
)


def _make_well(pos, rlu=100, cell_type="", et="", tumor=False):
    return Well(position=pos, row_idx=0, col_idx=0, rlu=rlu,
                cell_type=cell_type, et_ratio=et, is_tumor_only=tumor)


def test_wells_to_config_skips_unlabeled():
    wells = {
        "A1": _make_well("A1"),
        "B1": _make_well("B1", cell_type="KO", et="1:1"),
    }
    records = wells_to_config(wells)
    assert len(records) == 1
    assert records[0]["position"] == "B1"
    assert records[0]["cell_type"] == "KO"


def test_config_to_labels_filters_invalid():
    data = [
        {"position": "A1", "cell_type": "KO"},
        {"position": "Z99", "cell_type": "Bad"},  # 无效
        {"position": "B2", "cell_type": "Control", "is_tumor_only": True},
    ]
    labels, skipped = config_to_labels(data)
    assert "A1" in labels
    assert "B2" in labels
    assert "Z99" in skipped


def test_save_and_load_roundtrip():
    wells = {
        "A1": _make_well("A1", tumor=True),
        "B3": _make_well("B3", cell_type="A1-KO", et="5:1"),
    }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write("")
        tmp = f.name
    try:
        save_config(wells, tmp)
        labels, skipped = load_config(tmp)
        assert skipped == []
        assert labels["A1"]["is_tumor_only"]
        assert labels["B3"]["cell_type"] == "A1-KO"
    finally:
        os.unlink(tmp)


def test_apply_config():
    wells = {
        "A1": _make_well("A1"),
        "B2": _make_well("B2"),
    }
    labels = {"A1": {"cell_type": "KO", "et_ratio": "10:1", "is_tumor_only": False}}
    count = apply_config(wells, labels)
    assert count == 1
    assert wells["A1"].cell_type == "KO"
    assert wells["A1"].et_ratio == "10:1"
    assert wells["B2"].cell_type == ""


if __name__ == "__main__":
    test_wells_to_config_skips_unlabeled()
    test_config_to_labels_filters_invalid()
    test_save_and_load_roundtrip()
    test_apply_config()
    print("All config tests passed!")
