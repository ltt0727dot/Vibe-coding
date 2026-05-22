"""96 孔板 Canvas 网格组件"""

import tkinter as tk
from typing import Dict, List, Optional, Set

from model import Well, ROW_LABELS, COL_COUNT

# 视觉常量
CELL_W = 64
CELL_H = 44
LABEL_W = 28
HEADER_H = 24
MARGIN = 4

CELL_COLORS = {
    "tumor-only": "#9CA3AF",
    "AAVS1_KO": "#FECACA",
    "Target gene_KO": "#FED7AA",
    "default": "#FFFFFF",
}
CUSTOM_COLORS = [
    "#DBEAFE", "#D1FAE5", "#EDE9FE", "#FEF3C7", "#CCFBF1", "#FCE7F3",
]

COLOR_ASSIGNED = {}  # cell_type → color, 动态分配


def get_cell_color(well: Well) -> str:
    """根据孔位标注返回背景色"""
    if well.is_tumor_only:
        return CELL_COLORS["tumor-only"]
    if not well.cell_type:
        return CELL_COLORS["default"]
    if well.cell_type in CELL_COLORS:
        return CELL_COLORS[well.cell_type]
    if well.cell_type not in COLOR_ASSIGNED:
        idx = len(COLOR_ASSIGNED)
        COLOR_ASSIGNED[well.cell_type] = CUSTOM_COLORS[idx % len(CUSTOM_COLORS)]
    return COLOR_ASSIGNED[well.cell_type]


class PlateView(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#FFFFFF", **kwargs)
        self.wells: Dict[str, Well] = {}
        self.selected: Set[str] = set()
        self._hovered_pos = None
        self._tooltip = None
        self._shift_anchor = None

        self._build_canvas()

    def _build_canvas(self):
        total_w = LABEL_W + COL_COUNT * CELL_W + MARGIN * 2
        total_h = HEADER_H + 8 * CELL_H + MARGIN * 2

        self.canvas = tk.Canvas(
            self, bg="#FFFFFF", width=total_w, height=total_h,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        vbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(
            xscrollcommand=hbar.set, yscrollcommand=vbar.set,
            scrollregion=(0, 0, total_w, total_h),
        )

        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_click)

    def set_wells(self, wells: Dict[str, Well]):
        self.wells = wells
        self.selected.clear()
        self._shift_anchor = None
        COLOR_ASSIGNED.clear()
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        if not self.wells:
            self._draw_empty()
            return
        self._draw_grid()

    def _draw_empty(self):
        x = LABEL_W + COL_COUNT * CELL_W / 2
        y = HEADER_H + 8 * CELL_H / 2
        self.canvas.create_text(
            x, y, text="请选择 Excel 文件加载数据",
            fill="#94A3B8", font=("Microsoft YaHei", 12),
        )

    def _well_rect(self, row: int, col: int) -> tuple:
        """返回孔位的 (x1, y1, x2, y2)"""
        x1 = LABEL_W + col * CELL_W + MARGIN
        y1 = HEADER_H + row * CELL_H + MARGIN
        return (x1, y1, x1 + CELL_W, y1 + CELL_H)

    def _draw_grid(self):
        # 列标题
        for c in range(COL_COUNT):
            x = LABEL_W + c * CELL_W + CELL_W / 2 + MARGIN
            y = HEADER_H / 2
            self.canvas.create_text(
                x, y, text=str(c + 1),
                fill="#334155", font=("Microsoft YaHei", 9, "bold"),
            )

        for r in range(8):
            # 行标签
            x = LABEL_W / 2
            y = HEADER_H + r * CELL_H + CELL_H / 2 + MARGIN
            self.canvas.create_text(
                x, y, text=ROW_LABELS[r],
                fill="#334155", font=("Microsoft YaHei", 9, "bold"),
            )

            for c in range(COL_COUNT):
                pos = f"{ROW_LABELS[r]}{c + 1}"
                well = self.wells.get(pos)
                if not well:
                    continue
                x1, y1, x2, y2 = self._well_rect(r, c)
                color = get_cell_color(well)
                outline = "#2563EB" if pos in self.selected else ""
                outline_w = 2 if pos in self.selected else 0

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline=outline, width=outline_w,
                    tags=("cell", pos),
                )
                self.canvas.create_text(
                    x1 + CELL_W / 2, y1 + CELL_H / 2,
                    text=str(int(well.rlu)),
                    fill="#1E293B",
                    font=("Microsoft YaHei", 9),
                    tags=("cell", pos),
                )

    def _on_mouse_move(self, event):
        """鼠标悬停检测"""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        r, c = self._xy_to_rc(cx, cy)
        if r is not None:
            pos = f"{ROW_LABELS[r]}{c + 1}"
            if pos != self._hovered_pos:
                self._hovered_pos = pos
                self._update_tooltip(pos)
        else:
            self._hovered_pos = None
            self._hide_tooltip()

    def _on_click(self, event):
        """鼠标点击选择"""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        r, c = self._xy_to_rc(cx, cy)
        if r is None:
            return
        pos = f"{ROW_LABELS[r]}{c + 1}"

        if event.state & 0x0004:  # Ctrl
            if pos in self.selected:
                self.selected.discard(pos)
            else:
                self.selected.add(pos)
            self._shift_anchor = (r, c)
        elif event.state & 0x0001:  # Shift
            if self._shift_anchor:
                sr, sc = self._shift_anchor
                r1, r2 = sorted([sr, r])
                c1, c2 = sorted([sc, c])
                self.selected.clear()
                for ri in range(r1, r2 + 1):
                    for ci in range(c1, c2 + 1):
                        self.selected.add(f"{ROW_LABELS[ri]}{ci + 1}")
            else:
                self.selected.add(pos)
                self._shift_anchor = (r, c)
        else:
            self.selected = {pos}
            self._shift_anchor = (r, c)
        self.redraw()

    def _xy_to_rc(self, x: float, y: float):
        """画布坐标 → (row, col)，超出范围返回 None"""
        col = int((x - LABEL_W - MARGIN) / CELL_W)
        row = int((y - HEADER_H - MARGIN) / CELL_H)
        if 0 <= row < 8 and 0 <= col < COL_COUNT:
            return (row, col)
        return None

    def _update_tooltip(self, pos: str):
        self._hide_tooltip()
        well = self.wells.get(pos)
        if not well:
            return
        lines = [
            f"孔位: {pos}",
            f"RLU: {int(well.rlu)}",
        ]
        if well.is_tumor_only:
            lines.append("类型: tumor-only")
        elif well.cell_type:
            lines.append(f"类型: {well.cell_type}")
            if well.et_ratio:
                lines.append(f"E:T: {well.et_ratio}")

        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.attributes("-topmost", True)
        frame = tk.Frame(self._tooltip, bg="#1E293B", padx=8, pady=4)
        frame.pack()
        for line in lines:
            tk.Label(
                frame, text=line, bg="#1E293B", fg="#FFFFFF",
                font=("Microsoft YaHei", 9),
            ).pack(anchor=tk.W)
        # 定位到鼠标附近
        x = self.winfo_pointerx() + 16
        y = self.winfo_pointery() + 8
        self._tooltip.geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None
