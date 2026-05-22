"""Excel 文件读取与 96 孔板数据解析（纯 stdlib，无外部依赖）"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from model import Well, ROW_LABELS, COL_COUNT

XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    """读取 xlsx 共享字符串表"""
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    tree = ET.parse(zf.open("xl/sharedStrings.xml"))
    strings = []
    for si in tree.findall(f".//{{{XLSX_NS}}}si"):
        texts = []
        for t in si.iter(f"{{{XLSX_NS}}}t"):
            if t.text:
                texts.append(t.text)
        strings.append("".join(texts))
    return strings


def _cell_value(cell: ET.Element, ss: List[str]) -> Optional[str]:
    """获取单元格的字符串值（有共享字符串引用则解析，否则用原始数值）"""
    v = cell.find(f"ns:v", {"ns": XLSX_NS})
    if v is None or v.text is None:
        return None
    if cell.get("t") == "s":
        idx = int(v.text)
        return ss[idx] if 0 <= idx < len(ss) else None
    return v.text


def _col_letter_to_index(letter: str) -> int:
    """列字母转 0-based 索引，如 A→0, B→1"""
    return ord(letter.upper()) - ord("A")


def parse_xlsx(filepath: str) -> Dict[str, Well]:
    """解析 xlsx 文件，返回 {position: Well} 字典

    自动检测数据起始行：搜索连续 8 行，第一列值为 A-H 的行。
    从该行开始的 8 行，相邻列包含 12 个数值。
    """
    zf = zipfile.ZipFile(filepath, "r")
    ss = _read_shared_strings(zf)
    sheet = ET.parse(zf.open("xl/worksheets/sheet1.xml"))
    zf.close()

    # 收集所有行的数据：row_num → {col_letter: value_str}
    rows_data: Dict[int, Dict[str, Optional[str]]] = {}
    for row in sheet.findall(f".//{{{XLSX_NS}}}row"):
        row_num = int(row.get("r"))
        cells: Dict[str, Optional[str]] = {}
        for cell in row.findall(f"ns:c", {"ns": XLSX_NS}):
            ref = cell.get("r")
            col_letter = ref.rstrip("0123456789")
            cells[col_letter] = _cell_value(cell, ss)
        rows_data[row_num] = cells

    # 构建每行的列值列表（从 A 列开始到最大列）
    max_col = max(
        max((_col_letter_to_index(c) for c in row.keys()), default=-1)
        for row in rows_data.values()
    )

    def row_values(row: Dict[str, Optional[str]]) -> List[Optional[str]]:
        return [row.get(chr(ord("A") + i)) for i in range(max_col + 1)]

    # 搜索数据区域：A-H 在同一列纵向排列，连续 8 行
    # 对每列检查是否包含 A-H 序列
    sorted_rows = sorted(rows_data.keys())
    data_start_row = None
    data_start_col = None

    for col_idx in range(max_col + 1):
        col_letter = chr(ord("A") + col_idx)
        # 收集该列所有行的值
        col_values = []
        for row_num in sorted_rows:
            rv = row_values(rows_data[row_num])
            col_values.append((row_num, rv[col_idx] if col_idx < len(rv) else None))

        for i in range(len(col_values) - 7):
            chunk = [col_values[i + j][1] for j in range(8)]
            if all(
                chunk[j] == ROW_LABELS[j] for j in range(8)
            ):
                data_start_row = col_values[i][0]
                data_start_col = col_idx
                break
        if data_start_row is not None:
            break

    if data_start_row is None:
        raise ValueError("未找到 96 孔板数据区域（A-H 行标签）")

    # 提取 8×12 RLU 矩阵
    data_start_col_rlu = data_start_col + 1  # 行标签列右边是数值列
    wells: dict[str, Well] = {}

    for i in range(8):
        row_num = data_start_row + i
        rv = row_values(rows_data.get(row_num, {}))
        for j in range(COL_COUNT):
            col = data_start_col_rlu + j
            val_str = rv[col] if col < len(rv) else None
            try:
                rlu = float(val_str) if val_str is not None else 0.0
            except (ValueError, TypeError):
                rlu = 0.0
            position = f"{ROW_LABELS[i]}{j + 1}"
            wells[position] = Well(
                position=position, row_idx=i, col_idx=j, rlu=rlu
            )

    return wells
