"""JSON 配置存取"""

import json
import os
from typing import Dict

from model import Well, ROW_LABELS, COL_COUNT


def wells_to_config(wells: Dict[str, Well]) -> list:
    """将标注信息序列化为可 JSON 存储的列表"""
    records = []
    for pos, w in wells.items():
        if w.is_labeled:
            records.append({
                "position": pos,
                "cell_type": w.cell_type,
                "et_ratio": w.et_ratio,
                "is_tumor_only": w.is_tumor_only,
            })
    return records


def config_to_labels(config: list) -> Dict[str, dict]:
    """解析配置列表，返回 {position: label_dict}，过滤无效孔位"""
    labels = {}
    skipped = []
    for item in config:
        pos = item.get("position", "")
        if not pos or not isinstance(pos, str) or len(pos) < 2:
            continue
        row = pos[0].upper()
        try:
            col = int(pos[1:])
        except ValueError:
            skipped.append(pos)
            continue
        if row not in ROW_LABELS or not (1 <= col <= COL_COUNT):
            skipped.append(pos)
            continue
        labels[pos] = {
            "cell_type": item.get("cell_type", ""),
            "et_ratio": item.get("et_ratio", ""),
            "is_tumor_only": item.get("is_tumor_only", False),
        }
    return labels, skipped


def save_config(wells: Dict[str, Well], filepath: str):
    """保存标注配置为 JSON 文件"""
    data = wells_to_config(wells)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config(filepath: str) -> Dict[str, dict]:
    """从 JSON 文件加载标注配置，返回 {position: label_dict}"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return config_to_labels(data)


def apply_config(wells: Dict[str, Well], labels: Dict[str, dict]) -> int:
    """将加载的标注配置应用到 wells 字典，返回应用的孔数"""
    count = 0
    for pos, info in labels.items():
        well = wells.get(pos)
        if well:
            well.cell_type = info.get("cell_type", "")
            well.et_ratio = info.get("et_ratio", "")
            well.is_tumor_only = info.get("is_tumor_only", False)
            count += 1
    return count
