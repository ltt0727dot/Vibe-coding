"""主界面布局"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser

from reader import parse_xlsx
from plate_view import PlateView
from label_panel import LabelPanel
from config import save_config, load_config, apply_config
from analysis import compute_killing, anova_two_way
from charts import create_main_chart, create_compare_chart, get_default_color
from export import export_results_xlsx, save_figure

WINDOW_TITLE = "CAR-T 杀伤分析工具"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WIDTH = 1024
MIN_HEIGHT = 768

PRIMARY = "#1A365D"
PRIMARY_LIGHT = "#DBEAFE"
BG = "#F8FAFC"
TEXT = "#1E293B"
TEXT_LIGHT = "#64748B"
WHITE = "#FFFFFF"
GREEN = "#16A34A"

FONT = ("Microsoft YaHei", 9)
FONT_BOLD = ("Microsoft YaHei", 9, "bold")
FONT_LARGE = ("Microsoft YaHei", 11, "bold")
FONT_TITLE = ("Microsoft YaHei", 14, "bold")


class RoundedButton(tk.Canvas):
    """Canvas 自绘圆角按钮（不使用 smooth 参数确保 Windows 兼容）"""

    def __init__(self, parent, text="", command=None, bg=PRIMARY, fg=WHITE,
                 font=FONT, radius=8, width=120, height=32, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bd=0, **kwargs)
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._font = font
        self._radius = radius
        self._btn_w = width
        self._btn_h = height
        self._hover = False
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.after(1, self._draw)

    def _draw(self):
        try:
            self.delete("all")
        except tk.TclError:
            return
        r = self._radius
        w, h = self._btn_w, self._btn_h
        color = _lighten(self._bg) if self._hover else self._bg
        # 用多个矩形 + 四角小椭圆模拟圆角矩形
        self.create_rectangle(r, 0, w - r, h, fill=color, outline="", tags="bg")
        self.create_rectangle(0, r, w, h - r, fill=color, outline="", tags="bg")
        # 四角椭圆
        d = r * 2
        self.create_oval(0, 0, d, d, fill=color, outline="", tags="bg")
        self.create_oval(w - d, 0, w, d, fill=color, outline="", tags="bg")
        self.create_oval(0, h - d, d, h, fill=color, outline="", tags="bg")
        self.create_oval(w - d, h - d, w, h, fill=color, outline="", tags="bg")
        self.create_text(w / 2, h / 2, text=self._text,
                         fill=self._fg, font=self._font, tags="text")

    def _on_click(self, event):
        if self._command:
            self._command()

    def _on_enter(self, event):
        self._hover = True
        self._draw()

    def _on_leave(self, event):
        self._hover = False
        self._draw()


def _lighten(hex_color):
    try:
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = min(255, r + 20); g = min(255, g + 20); b = min(255, b + 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return hex_color


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=BG)

        self._set_app_icon()

        self.wells = None
        self.results = None
        self.group_stats = None
        self.t_only_mean = None
        self.color_map = {}  # cell_type → hex color
        self._main_chart_canvas = None
        self._main_chart_fig = None
        self._compare_chart_canvas = None
        self._compare_chart_fig = None
        self._main_chart_frame = None
        self._post_hoc = None
        self._anova_result = None

        self._build_ui()
        self._start_selection_poll()

    def _set_app_icon(self):
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.dirname(__file__))
        png_path = os.path.join(base, "resources", "icon.png")
        ico_path = os.path.join(base, "resources", "icon.ico")
        try:
            if os.path.exists(png_path):
                img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, img)
                self._icon_img = img  # keep reference
            elif os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except tk.TclError:
            pass

    # ── 构建 UI ───────────────────────────────────────────

    def _build_ui(self):
        self._build_toolbar()

        self.paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4
        )
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # 左侧：96 孔板
        self.plate_view = PlateView(self.paned)
        self.paned.add(self.plate_view, width=int(WINDOW_WIDTH * 0.7))

        # 右侧
        self._build_right_panel()

        # 状态栏
        self.status_var = tk.StringVar(value="就绪 — 请选择 Excel 文件")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bg=PRIMARY, fg=WHITE, anchor=tk.W, padx=10, font=FONT,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=PRIMARY, padx=10, pady=8)
        toolbar.pack(fill=tk.X)

        tk.Label(
            toolbar, text="CAR-T 杀伤分析", bg=PRIMARY, fg=WHITE, font=FONT_TITLE,
        ).pack(side=tk.LEFT, padx=(0, 20))

        self.btn_open = RoundedButton(
            toolbar, text="选择 Excel 文件", command=self._on_open_file,
            bg=WHITE, fg=PRIMARY, font=FONT_BOLD, width=140, height=34,
        )
        self.btn_open.pack(side=tk.LEFT, padx=4)

        self.filepath_var = tk.StringVar()
        tk.Label(
            toolbar, textvariable=self.filepath_var,
            bg=PRIMARY, fg=PRIMARY_LIGHT, font=FONT,
        ).pack(side=tk.LEFT, padx=10)

    def _build_right_panel(self):
        right_outer = tk.Frame(self.paned, bg=BG)
        self.paned.add(right_outer, width=int(WINDOW_WIDTH * 0.3))

        right_canvas = tk.Canvas(right_outer, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(right_outer, orient=tk.VERTICAL, command=right_canvas.yview)
        self.right_scroll = tk.Frame(right_canvas, bg=BG)

        self.right_scroll.bind("<Configure>",
            lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        right_canvas.create_window((0, 0), window=self.right_scroll, anchor=tk.NW)
        right_canvas.configure(yscrollcommand=scrollbar.set)

        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.bind("<Enter>", lambda e: right_canvas.bind_all("<MouseWheel>",
            lambda ev: right_canvas.yview_scroll(int(-1*(ev.delta/120)), "units")))
        right_canvas.bind("<Leave>", lambda e: right_canvas.unbind_all("<MouseWheel>"))

        # 标注面板
        self.label_panel = LabelPanel(
            self.right_scroll, on_apply=self._on_apply_label
        )
        self.label_panel.pack(fill=tk.X, padx=2, pady=2)

        # 绑定按钮
        self.label_panel.btn_save.configure(command=self._on_save_config)
        self.label_panel.btn_load.configure(command=self._on_load_config)
        self.label_panel.btn_analyze.configure(command=self._on_analyze)

        # 图表结果区
        self.result_frame = tk.Frame(self.right_scroll, bg=BG)

    # ── 事件处理 ──────────────────────────────────────────

    def _on_open_file(self):
        path = filedialog.askopenfilename(
            title="选择酶标仪导出文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self.filepath_var.set(path)
        self._input_path = path  # 保存路径用于生成输出文件名
        try:
            self.wells = parse_xlsx(path)
            self.plate_view.set_wells(self.wells)
            self.status_var.set(f"已加载: {os.path.basename(path)} — 共 {len(self.wells)} 个孔位")
        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    def _on_apply_label(self, cell_type, et_ratio, is_tumor_only):
        if not self.wells:
            return
        selected = self.plate_view.selected
        if not selected:
            self.status_var.set("请先在孔板上选择要标注的孔位")
            return
        for pos in selected:
            well = self.wells.get(pos)
            if well:
                well.cell_type = cell_type
                well.et_ratio = et_ratio
                well.is_tumor_only = is_tumor_only
        count = len(selected)
        label = "tumor-only" if is_tumor_only else f"{cell_type} / {et_ratio}"
        self.status_var.set(f"已标注 {count} 个孔为: {label}")
        self.plate_view.redraw()

    def _on_save_config(self):
        if not self.wells:
            return
        path = filedialog.asksaveasfilename(
            title="保存标注配置", defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
        )
        if not path:
            return
        try:
            save_config(self.wells, path)
            self.status_var.set(f"配置已保存: {path}")
        except Exception as e:
            messagebox.showerror("保存配置失败", str(e))

    def _on_load_config(self):
        if not self.wells:
            messagebox.showinfo("提示", "请先加载 Excel 文件")
            return
        path = filedialog.askopenfilename(
            title="加载标注配置",
            filetypes=[("JSON 文件", "*.json")],
        )
        if not path:
            return
        has_labels = any(w.is_labeled for w in self.wells.values())
        if has_labels:
            if not messagebox.askyesno("确认覆盖", "当前孔板已有标注，是否覆盖？"):
                return
        try:
            labels, skipped = load_config(path)
            count = apply_config(self.wells, labels)
            msg = f"已应用 {count} 个孔的标注"
            if skipped:
                msg += f"，忽略 {len(skipped)} 个越界孔位"
            self.status_var.set(msg)
            self.plate_view.redraw()
        except Exception as e:
            messagebox.showerror("加载配置失败", str(e))

    def _on_analyze(self):
        if not self.wells:
            return
        try:
            self.results, self.t_only_mean, self.group_stats = compute_killing(self.wells)
        except ValueError as e:
            messagebox.showerror("分析失败", str(e))
            return

        self.status_var.set(
            f"分析完成 — T_only_mean={self.t_only_mean:.1f}，{len(self.group_stats)} 个分组"
        )
        self._clear_result_area()
        self._show_results()

    # ── 结果区域 ──────────────────────────────────────────

    def _clear_result_area(self):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        self.result_frame.pack_forget()
        self._main_chart_canvas = self._main_chart_fig = None
        self._compare_chart_canvas = self._compare_chart_fig = None
        self._main_chart_frame = None
        self._post_hoc = None
        self._anova_result = None

    def _show_results(self):
        self.result_frame.pack(fill=tk.X, padx=2, pady=(8, 2), after=self.label_panel)

        cell_types = sorted(set(g.cell_type for g in self.group_stats))
        # 初始化/更新 color_map 中的默认颜色
        for idx, ct in enumerate(cell_types):
            if ct not in self.color_map:
                self.color_map[ct] = get_default_color(ct, idx)

        # ── 主图 ──
        main_f = tk.Frame(self.result_frame, bg=WHITE, relief=tk.SUNKEN, bd=1)
        main_f.pack(fill=tk.X, pady=4)

        # 主图 标题 + 坐标轴编辑
        edit_f1 = tk.Frame(main_f, bg=WHITE)
        edit_f1.pack(fill=tk.X, padx=4, pady=(4, 0))

        tk.Label(edit_f1, text="标题:", bg=WHITE, font=FONT).pack(side=tk.LEFT)
        self.main_title_var = tk.StringVar(value="CAR-T 杀伤曲线")
        tk.Entry(edit_f1, textvariable=self.main_title_var, font=FONT,
                 width=18).pack(side=tk.LEFT, padx=2)

        tk.Label(edit_f1, text="X:", bg=WHITE, font=FONT).pack(side=tk.LEFT, padx=(6, 0))
        self.main_xlabel_var = tk.StringVar(value="E:T")
        tk.Entry(edit_f1, textvariable=self.main_xlabel_var, font=FONT,
                 width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(edit_f1, text="Y:", bg=WHITE, font=FONT).pack(side=tk.LEFT, padx=(4, 0))
        self.main_ylabel_var = tk.StringVar(value="% of Cytolysis")
        tk.Entry(edit_f1, textvariable=self.main_ylabel_var, font=FONT,
                 width=10).pack(side=tk.LEFT, padx=2)

        RoundedButton(edit_f1, text="刷新", command=self._refresh_main_chart,
                      bg=PRIMARY, fg=WHITE, font=FONT_BOLD,
                      width=50, height=26).pack(side=tk.RIGHT, padx=2)

        self._main_chart_frame = tk.Frame(main_f, bg=WHITE)
        self._main_chart_frame.pack(fill=tk.X, padx=4, pady=2)
        self._refresh_main_chart()

        RoundedButton(
            main_f, text="下载主图为 PNG",
            command=self._save_main_chart,
            bg=WHITE, fg=PRIMARY, font=FONT, width=140, height=28,
        ).pack(pady=4)

        # ── 颜色调色板 ──
        palette_f = tk.Frame(self.result_frame, bg=BG)
        palette_f.pack(fill=tk.X, pady=6)
        tk.Label(palette_f, text="细胞类型颜色:", bg=BG, fg=TEXT, font=FONT_BOLD).pack(side=tk.LEFT)
        for ct in cell_types:
            color = self.color_map.get(ct, "#999")
            swatch = tk.Canvas(palette_f, width=20, height=20,
                               highlightthickness=0, bg=color)
            swatch.pack(side=tk.LEFT, padx=(6, 2))
            swatch.bind("<Button-1>", lambda e, ct=ct: self._pick_color(ct))
            tk.Label(palette_f, text=ct, bg=BG, fg=TEXT, font=FONT,
                     cursor="hand2").pack(side=tk.LEFT)
            # 也让文字可点击
            swatch.bind("<Button-1>", lambda e, c=ct: self._pick_color(c))

        # ── 对比图 ──
        compare_f = tk.Frame(self.result_frame, bg=WHITE, relief=tk.SUNKEN, bd=1)
        compare_f.pack(fill=tk.X, pady=4)

        # 对比图 标题 + 坐标轴编辑
        edit_f2 = tk.Frame(compare_f, bg=WHITE)
        edit_f2.pack(fill=tk.X, padx=4, pady=(4, 0))

        tk.Label(edit_f2, text="标题:", bg=WHITE, font=FONT).pack(side=tk.LEFT)
        self.compare_title_var = tk.StringVar(value="")
        tk.Entry(edit_f2, textvariable=self.compare_title_var, font=FONT,
                 width=18).pack(side=tk.LEFT, padx=2)

        tk.Label(edit_f2, text="X:", bg=WHITE, font=FONT).pack(side=tk.LEFT, padx=(6, 0))
        self.compare_xlabel_var = tk.StringVar(value="E:T")
        tk.Entry(edit_f2, textvariable=self.compare_xlabel_var, font=FONT,
                 width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(edit_f2, text="Y:", bg=WHITE, font=FONT).pack(side=tk.LEFT, padx=(4, 0))
        self.compare_ylabel_var = tk.StringVar(value="% of Cytolysis")
        tk.Entry(edit_f2, textvariable=self.compare_ylabel_var, font=FONT,
                 width=10).pack(side=tk.LEFT, padx=2)

        # 细胞类型选择
        sel_f = tk.Frame(compare_f, bg=WHITE)
        sel_f.pack(fill=tk.X, padx=4, pady=4)

        tk.Label(sel_f, text="对比:", bg=WHITE, font=FONT).pack(side=tk.LEFT)
        self.compare_var1 = tk.StringVar(value=cell_types[0] if cell_types else "")
        self.compare_var2 = tk.StringVar(value=cell_types[1] if len(cell_types) > 1 else "")
        cb1 = ttk.Combobox(sel_f, textvariable=self.compare_var1, values=cell_types,
                           state="readonly", width=14)
        cb1.pack(side=tk.LEFT, padx=2)
        tk.Label(sel_f, text="vs", bg=WHITE, font=FONT).pack(side=tk.LEFT)
        cb2 = ttk.Combobox(sel_f, textvariable=self.compare_var2, values=cell_types,
                           state="readonly", width=14)
        cb2.pack(side=tk.LEFT, padx=2)

        RoundedButton(sel_f, text="更新 (含ANOVA)", command=self._update_compare_chart,
                      bg=PRIMARY, fg=WHITE, font=FONT_BOLD,
                      width=120, height=26).pack(side=tk.LEFT, padx=6)

        self.compare_chart_frame = tk.Frame(compare_f, bg=WHITE)
        self.compare_chart_frame.pack(fill=tk.X, padx=4, pady=2)

        RoundedButton(
            compare_f, text="下载对比图为 PNG",
            command=self._save_compare_chart,
            bg=WHITE, fg=PRIMARY, font=FONT, width=150, height=28,
        ).pack(pady=4)

        # ── 导出按钮 ──
        export_f = tk.Frame(self.result_frame, bg=BG)
        export_f.pack(fill=tk.X, pady=6)

        RoundedButton(
            export_f, text="导出 XLSX (详细+Prism)",
            command=self._export_xlsx,
            bg=PRIMARY, fg=WHITE, font=FONT_BOLD, width=170, height=32,
        ).pack(side=tk.LEFT, padx=2)

        # 更新对比图
        self._update_compare_chart()

    def _refresh_main_chart(self):
        if not hasattr(self, "_main_chart_frame") or self._main_chart_frame is None:
            return
        for w in self._main_chart_frame.winfo_children():
            w.destroy()
        canvas, fig = create_main_chart(
            self._main_chart_frame, self.group_stats,
            title=self.main_title_var.get(),
            xlabel=self.main_xlabel_var.get(),
            ylabel=self.main_ylabel_var.get(),
            color_map=self.color_map,
        )
        canvas.get_tk_widget().pack(padx=4, pady=4)
        self._main_chart_canvas = canvas
        self._main_chart_fig = fig

    def _update_compare_chart(self):
        for w in self.compare_chart_frame.winfo_children():
            w.destroy()
        t1 = self.compare_var1.get()
        t2 = self.compare_var2.get()
        if not t1 or not t2:
            return

        # 运行 ANOVA
        self._post_hoc = None
        self._anova_result = None
        if self.results and t1 and t2:
            try:
                anova_table, anova_stats, post_hoc = anova_two_way(self.results, t1, t2)
                if not anova_table.empty:
                    self._anova_result = (anova_table, anova_stats)
                    self._post_hoc = post_hoc
            except Exception:
                pass

        canvas, fig = create_compare_chart(
            self.compare_chart_frame, self.group_stats, t1, t2,
            title=self.compare_title_var.get() or f"{t1} vs {t2}",
            xlabel=self.compare_xlabel_var.get(),
            ylabel=self.compare_ylabel_var.get(),
            color_map=self.color_map,
            post_hoc=self._post_hoc,
        )
        canvas.get_tk_widget().pack(padx=4, pady=4)
        self._compare_chart_canvas = canvas
        self._compare_chart_fig = fig

    def _pick_color(self, cell_type: str):
        _, color = colorchooser.askcolor(
            title=f"选择 {cell_type} 的颜色",
            initialcolor=self.color_map.get(cell_type, "#2563EB"),
        )
        if color:
            self.color_map[cell_type] = color
            # 刷新两个图表
            self._refresh_main_chart()
            self._update_compare_chart()

    def _save_main_chart(self):
        if self._main_chart_fig:
            path = save_figure(self._main_chart_fig, "killing_main_chart.png")
            if path:
                self.status_var.set(f"主图已保存: {path}")

    def _save_compare_chart(self):
        if self._compare_chart_fig:
            path = save_figure(self._compare_chart_fig, "killing_compare_chart.png")
            if path:
                self.status_var.set(f"对比图已保存: {path}")

    def _export_xlsx(self):
        if not self.results:
            return
        # 默认文件名：输入文件名 + "_results"
        default_name = "analysis_results.xlsx"
        if hasattr(self, "_input_path") and self._input_path:
            base = os.path.splitext(os.path.basename(self._input_path))[0]
            default_name = f"{base}_results.xlsx"

        path = filedialog.asksaveasfilename(
            title="导出分析结果 (XLSX)",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            export_results_xlsx(
                self.results, self.wells, self.group_stats, self.t_only_mean,
                path,
                compare_type1=self.compare_var1.get() if hasattr(self, "compare_var1") else "",
                compare_type2=self.compare_var2.get() if hasattr(self, "compare_var2") else "",
                anova_result=self._anova_result,
                post_hoc=self._post_hoc,
            )
            self.status_var.set(f"结果已导出: {path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _start_selection_poll(self):
        self._last_selected = set()
        self._poll_selection()

    def _poll_selection(self):
        if hasattr(self, "plate_view"):
            current = self.plate_view.selected
            if current != self._last_selected:
                self._last_selected = current.copy()
                self.label_panel.update_selected(current)
        self.root.after(200, self._poll_selection)

    def run(self):
        self.root.mainloop()
