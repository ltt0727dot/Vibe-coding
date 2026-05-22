"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional

ROW_LABELS = list("ABCDEFGH")
COL_COUNT = 12


@dataclass
class Well:
    """单个孔位数据"""
    position: str               # e.g. "A1"
    row_idx: int                # 0-7
    col_idx: int                # 0-11
    rlu: float                  # 原始发光值
    cell_type: str = ""         # 细胞类型标签
    et_ratio: str = ""          # E:T 比例，如 "5:1"
    is_tumor_only: bool = False # 是否为 tumor-only 孔

    @property
    def is_labeled(self) -> bool:
        return bool(self.cell_type) or self.is_tumor_only


@dataclass
class GroupStats:
    """分组统计结果"""
    cell_type: str
    et_ratio: str
    count: int
    mean_killing: float
    sd_killing: Optional[float]  # None if count==1


@dataclass
class WellResult:
    """单个孔的计算结果"""
    position: str
    cell_type: str
    et_ratio: str
    rlu: float
    t_only_mean: float
    killing_pct: float
    group_mean: float
    group_sd: Optional[float]
