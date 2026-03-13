"""
ui/settings_dialog.py - 설정 다이얼로그
우클릭 메뉴 또는 첫 실행 시 팝업됩니다.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class SettingsDialog(tk.Toplevel):
    """D2TZ Tracker 설정 창."""

    def __init__(
        self,
        parent: tk.Tk,
        cfg: dict,
        on_save: Callable[[dict], None],
        require_token: bool = False,
    ):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.on_save = on_save
        self.require_token = require_token

        self.title("D2TZ Tracker 설정")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()  # 모달 처리

        # 색상 테마
        BG = "#1a1a2e"
        FG = "#e0e0e0"
        ACCENT = "#f5a623"
        ENTRY_BG = "#16213e"

        self.configure(bg=BG)

        # ── 스타일 ──────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=BG)
        style.configure("Dark.TLabel", background=BG, foreground=FG, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=ACCENT, font=("Segoe UI", 11, "bold"))
        style.configure("Dark.TCheckbutton", background=BG, foreground=FG, font=("Segoe UI", 9))
        style.configure(
            "Accent.TButton",
            background=ACCENT, foreground="#1a1a2e",
            font=("Segoe UI", 9, "bold"), relief="flat",
        )
        style.map("Accent.TButton", background=[("active", "#d4891f")])
        style.configure(
            "Cancel.TButton",
            background="#444", foreground=FG,
            font=("Segoe UI", 9), relief="flat",
        )
        style.map("Cancel.TButton", background=[("active", "#555")])
        style.configure(
            "Dark.Horizontal.TScale",
            background=BG, troughcolor="#333", sliderlength=14,
        )

        # ── 레이아웃 ─────────────────────────────────────────────────────
        pad = {"padx": 14, "pady": 6}
        frame = ttk.Frame(self, style="Dark.TFrame", padding=16)
        frame.grid(sticky="nsew")

        # 제목
        ttk.Label(frame, text="⚙  D2TZ Tracker 설정", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        # ── 토큰 입력 ─────────────────────────────────────────────────
        ttk.Label(frame, text="API 토큰", style="Dark.TLabel").grid(
            row=1, column=0, sticky="w", **pad
        )

        self._token_var = tk.StringVar(value=self.cfg.get("token_d2tz", ""))
        self._token_entry = tk.Entry(
            frame, textvariable=self._token_var, width=36,
            bg=ENTRY_BG, fg=FG, insertbackground=FG,
            relief="flat", font=("Consolas", 9), show="*",
        )
        self._token_entry.grid(row=1, column=1, sticky="ew", **pad)

        # 토큰 표시/숨기기 토글
        self._show_token = tk.BooleanVar(value=False)
        show_btn = tk.Checkbutton(
            frame, text="표시", variable=self._show_token,
            command=self._toggle_token_visibility,
            bg=BG, fg=FG, selectcolor=ENTRY_BG,
            activebackground=BG, activeforeground=FG,
            relief="flat", font=("Segoe UI", 8),
        )
        show_btn.grid(row=1, column=2, padx=2)

        # 토큰 안내
        ttk.Label(
            frame, text="👉 d2tz.info/api 에서 Google Form으로 신청 (무료)",
            style="Dark.TLabel", foreground="#888", font=("Segoe UI", 8),
        ).grid(row=2, column=1, sticky="w", padx=14, pady=(0, 4))

        ttk.Separator(frame, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=8
        )

        # ── 언어 선택 ──────────────────────────────────────────────────
        ttk.Label(frame, text="구역명 표시", style="Dark.TLabel").grid(
            row=4, column=0, sticky="w"
        )
        self._language = tk.StringVar(value=self.cfg.get("language", "ko"))
        lang_frame = ttk.Frame(frame, style="Dark.TFrame")
        lang_frame.grid(row=4, column=1, sticky="w")
        ttk.Radiobutton(
            lang_frame, text="한글", variable=self._language,
            value="ko", style="Dark.TCheckbutton",
        ).pack(side="left")
        ttk.Radiobutton(
            lang_frame, text="English", variable=self._language,
            value="en", style="Dark.TCheckbutton",
        ).pack(side="left", padx=(10, 0))

        # ── 투명도 슬라이더 ───────────────────────────────────────────
        ttk.Label(frame, text="투명도", style="Dark.TLabel").grid(
            row=5, column=0, sticky="w", **pad
        )
        alpha_frame = ttk.Frame(frame, style="Dark.TFrame")
        alpha_frame.grid(row=5, column=1, sticky="ew")
        self._alpha = tk.DoubleVar(value=self.cfg.get("alpha", 0.85))
        alpha_slider = ttk.Scale(
            alpha_frame, from_=0.1, to=1.0, variable=self._alpha,
            orient="horizontal", length=160, style="Dark.Horizontal.TScale",
        )
        alpha_slider.pack(side="left")
        self._alpha_label = ttk.Label(
            alpha_frame, text=f"{self._alpha.get():.0%}", style="Dark.TLabel", width=5
        )
        self._alpha_label.pack(side="left", padx=(6, 0))
        self._alpha.trace_add("write", self._on_alpha_change)

        # ── Always on Top ─────────────────────────────────────────────
        self._always_on_top = tk.BooleanVar(value=self.cfg.get("always_on_top", True))
        ttk.Checkbutton(
            frame, text="항상 위 (Always on Top)",
            variable=self._always_on_top, style="Dark.TCheckbutton",
        ).grid(row=6, column=0, columnspan=2, sticky="w", padx=14)

        # ── Lock Position ─────────────────────────────────────────────
        self._lock_position = tk.BooleanVar(value=self.cfg.get("lock_position", False))
        ttk.Checkbutton(
            frame, text="위치 고정 (Lock Position)",
            variable=self._lock_position, style="Dark.TCheckbutton",
        ).grid(row=7, column=0, columnspan=2, sticky="w", padx=14, pady=(2, 0))

        ttk.Separator(frame, orient="horizontal").grid(
            row=8, column=0, columnspan=3, sticky="ew", pady=10
        )

        # ── 저장 / 취소 버튼 ──────────────────────────────────────────
        btn_frame = ttk.Frame(frame, style="Dark.TFrame")
        btn_frame.grid(row=9, column=0, columnspan=3, sticky="e")
        ttk.Button(btn_frame, text="저장", style="Accent.TButton", command=self._save).pack(
            side="right", padx=(6, 0), ipadx=10
        )
        if not require_token:
            ttk.Button(btn_frame, text="취소", style="Cancel.TButton", command=self.destroy).pack(
                side="right", ipadx=6
            )

        # 창 중앙 배치
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # ── 콜백 ─────────────────────────────────────────────────────────────

    def _toggle_token_visibility(self) -> None:
        self._token_entry.configure(show="" if self._show_token.get() else "*")

    def _on_alpha_change(self, *_) -> None:
        val = self._alpha.get()
        self._alpha_label.configure(text=f"{val:.0%}")
        try:
            self.master.wm_attributes("-alpha", val)
        except Exception:
            pass

    def _save(self) -> None:
        token = self._token_var.get().strip()
        if not token:
            messagebox.showwarning(
                "토큰 필요",
                "API 토큰을 입력해주세요.\n\n"
                "d2tz.info/api 에서 Google Form으로 신청할 수 있습니다.",
                parent=self,
            )
            return

        self.cfg["token_d2tz"] = token
        self.cfg.update({
            "language": self._language.get(),
            "alpha": round(self._alpha.get(), 2),
            "always_on_top": self._always_on_top.get(),
            "lock_position": self._lock_position.get(),
        })
        self.on_save(self.cfg)
        self.destroy()
