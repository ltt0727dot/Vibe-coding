"""右侧标注面板"""

import tkinter as tk
from tkinter import messagebox
from typing import Dict, Set, Callable

PRESET_CELL_TYPES = ["AAVS1_KO", "Target gene_KO", "自定义"]
PRESET_ET_RATIOS = ["1:1", "1:2", "1:4", "1:8", "1:16", "1:32", "1:64", "1:128"]


class LabelPanel(tk.Frame):
    def __init__(self, parent, on_apply: Callable = None, **kwargs):
        super().__init__(parent, bg="#F8FAFC", **kwargs)
        self.on_apply = on_apply
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}

        # 已选孔位
        tk.Label(
            self, text="已选孔位", bg="#F8FAFC", fg="#1E293B",
            font=("Microsoft YaHei", 11, "bold"),
        ).pack(anchor=tk.W, **pad)

        self.selected_var = tk.StringVar(value="（未选择）")
        tk.Label(
            self, textvariable=self.selected_var,
            bg="#FFFFFF", fg="#64748B", anchor=tk.W, justify=tk.LEFT,
            font=("Microsoft YaHei", 9), relief=tk.SUNKEN, bd=1,
            wraplength=280, height=3,
        ).pack(fill=tk.X, **pad)

        # 分隔
        tk.Frame(self, bg="#E2E8F0", height=1).pack(fill=tk.X, padx=10, pady=8)

        # 细胞类型
        tk.Label(
            self, text="细胞类型", bg="#F8FAFC", fg="#1E293B",
            font=("Microsoft YaHei", 10),
        ).pack(anchor=tk.W, **pad)

        self.cell_type_var = tk.StringVar(value=PRESET_CELL_TYPES[0])
        self.cell_type_combo = tk.OptionMenu(
            self, self.cell_type_var, *PRESET_CELL_TYPES,
        )
        self.cell_type_combo.configure(
            font=("Microsoft YaHei", 9),
        )
        self.cell_type_combo.pack(fill=tk.X, **pad)

        # 自定义细胞类型
        custom_frame = tk.Frame(self, bg="#F8FAFC")
        custom_frame.pack(fill=tk.X, **pad)
        self.custom_type_entry = tk.Entry(
            custom_frame, font=("Microsoft YaHei", 9), width=16,
        )
        self.custom_type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.custom_type_entry.insert(0, "自定义类型...")
        self.custom_type_entry.bind("<FocusIn>", lambda e: self._clear_placeholder(
            self.custom_type_entry, "自定义类型..."
        ))
        self.custom_type_entry.bind("<FocusOut>", lambda e: self._restore_placeholder(
            self.custom_type_entry, "自定义类型..."
        ))

        btn_add_type = tk.Button(
            custom_frame, text="添加",
            command=self._add_custom_type,
            bg="#1A365D", fg="#FFFFFF",
            font=("Microsoft YaHei", 8), padx=8,
            cursor="hand2",
        )
        btn_add_type.pack(side=tk.LEFT, padx=(4, 0))

        # E:T 比例
        tk.Label(
            self, text="E:T 比例", bg="#F8FAFC", fg="#1E293B",
            font=("Microsoft YaHei", 10),
        ).pack(anchor=tk.W, **pad)

        self.et_var = tk.StringVar(value=PRESET_ET_RATIOS[0])
        self.et_combo = tk.OptionMenu(self, self.et_var, *PRESET_ET_RATIOS)
        self.et_combo.configure(font=("Microsoft YaHei", 9))
        self.et_combo.pack(fill=tk.X, **pad)

        # 自定义 E:T
        et_custom_frame = tk.Frame(self, bg="#F8FAFC")
        et_custom_frame.pack(fill=tk.X, **pad)
        self.custom_et_entry = tk.Entry(
            et_custom_frame, font=("Microsoft YaHei", 9), width=16,
        )
        self.custom_et_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.custom_et_entry.insert(0, "自定义比例...")
        self.custom_et_entry.bind("<FocusIn>", lambda e: self._clear_placeholder(
            self.custom_et_entry, "自定义比例..."
        ))
        self.custom_et_entry.bind("<FocusOut>", lambda e: self._restore_placeholder(
            self.custom_et_entry, "自定义比例..."
        ))

        btn_add_et = tk.Button(
            et_custom_frame, text="添加",
            command=self._add_custom_et,
            bg="#1A365D", fg="#FFFFFF",
            font=("Microsoft YaHei", 8), padx=8,
            cursor="hand2",
        )
        btn_add_et.pack(side=tk.LEFT, padx=(4, 0))

        # tumor-only 复选框
        self.tumor_only_var = tk.BooleanVar(value=False)
        self.tumor_only_cb = tk.Checkbutton(
            self, text="标记为 tumor-only（仅肿瘤，用于分母）",
            variable=self.tumor_only_var,
            command=self._on_tumor_only_toggle,
            bg="#F8FAFC", font=("Microsoft YaHei", 9),
        )
        self.tumor_only_cb.pack(anchor=tk.W, **pad)

        # 应用按钮
        tk.Frame(self, bg="#E2E8F0", height=1).pack(fill=tk.X, padx=10, pady=6)

        self.btn_apply = tk.Button(
            self, text="应用标注",
            command=self._on_apply,
            bg="#1A365D", fg="#FFFFFF",
            font=("Microsoft YaHei", 11, "bold"),
            padx=20, pady=6,
            cursor="hand2",
        )
        self.btn_apply.pack(fill=tk.X, padx=10, pady=4)

        # 配置按钮
        config_frame = tk.Frame(self, bg="#F8FAFC")
        config_frame.pack(fill=tk.X, padx=10, pady=4)
        self.btn_save = tk.Button(
            config_frame, text="保存配置",
            bg="#FFFFFF", fg="#1A365D",
            font=("Microsoft YaHei", 9), padx=8,
            cursor="hand2",
        )
        self.btn_save.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_load = tk.Button(
            config_frame, text="加载配置",
            bg="#FFFFFF", fg="#1A365D",
            font=("Microsoft YaHei", 9), padx=8,
            cursor="hand2",
        )
        self.btn_load.pack(side=tk.LEFT)

        # 分析按钮
        tk.Frame(self, bg="#E2E8F0", height=1).pack(fill=tk.X, padx=10, pady=8)

        self.btn_analyze = tk.Button(
            self, text="开始分析",
            bg="#16A34A", fg="#FFFFFF",
            font=("Microsoft YaHei", 11, "bold"),
            padx=20, pady=8,
            cursor="hand2",
        )
        self.btn_analyze.pack(fill=tk.X, padx=10, pady=4)

    def update_selected(self, positions: Set[str]):
        """更新已选孔位列表显示"""
        if not positions:
            self.selected_var.set("（未选择）")
        else:
            sorted_pos = sorted(
                positions,
                key=lambda p: (p[0], int(p[1:])),
            )
            text = ", ".join(sorted_pos)
            if len(text) > 60:
                text = text[:57] + "..."
            self.selected_var.set(text)

    def _clear_placeholder(self, entry: tk.Entry, placeholder: str):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.configure(fg="#1E293B")

    def _restore_placeholder(self, entry: tk.Entry, placeholder: str):
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)
            entry.configure(fg="#94A3B8")

    def _add_custom_type(self):
        text = self.custom_type_entry.get().strip()
        if not text or text == "自定义类型...":
            return
        menu = self.cell_type_combo["menu"]
        options = PRESET_CELL_TYPES[:]
        # 获取当前菜单项
        existing = []
        for i in range(menu.index("end") + 1):
            try:
                existing.append(menu.entrycget(i, "label"))
            except tk.TclError:
                pass
        if text not in existing:
            menu.add_command(
                label=text,
                command=lambda v=text: self.cell_type_var.set(v),
            )
        self.cell_type_var.set(text)
        self.custom_type_entry.delete(0, tk.END)
        self.custom_type_entry.insert(0, "自定义类型...")
        self.custom_type_entry.configure(fg="#94A3B8")

    def _add_custom_et(self):
        text = self.custom_et_entry.get().strip()
        if not text or text == "自定义比例...":
            return
        menu = self.et_combo["menu"]
        existing = []
        for i in range(menu.index("end") + 1):
            try:
                existing.append(menu.entrycget(i, "label"))
            except tk.TclError:
                pass
        if text not in existing:
            menu.add_command(
                label=text,
                command=lambda v=text: self.et_var.set(v),
            )
        self.et_var.set(text)
        self.custom_et_entry.delete(0, tk.END)
        self.custom_et_entry.insert(0, "自定义比例...")
        self.custom_et_entry.configure(fg="#94A3B8")

    def _on_tumor_only_toggle(self):
        if self.tumor_only_var.get():
            self.cell_type_combo.configure(state="disabled")
            self.et_combo.configure(state="disabled")
            self.custom_type_entry.configure(state="disabled")
            self.custom_et_entry.configure(state="disabled")
        else:
            self.cell_type_combo.configure(state="normal")
            self.et_combo.configure(state="normal")
            self.custom_type_entry.configure(state="normal")
            self.custom_et_entry.configure(state="normal")

    def _on_apply(self):
        if self.on_apply:
            cell_type = (
                "" if self.tumor_only_var.get()
                else self.cell_type_var.get()
            )
            et_ratio = (
                "" if self.tumor_only_var.get()
                else self.et_var.get()
            )
            self.on_apply(
                cell_type=cell_type,
                et_ratio=et_ratio,
                is_tumor_only=self.tumor_only_var.get(),
            )
