"""
ui/overlay.py - 메인 오버레이 창
프레임리스 투명 창으로 현재/다음 공포구역과 카운트다운을 표시합니다.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from api.client import fetch_terror_zone, TZInfo
from core.config import load_config, save_config
from core.tz_data import get_display_name, get_act
from ui.settings_dialog import SettingsDialog


# ─────────────────── 오버레이 색상/폰트 상수 ────────────────────────────
BG_COLOR      = "#0d0d1a"      # 창 배경
ACCENT_COLOR  = "#f5a623"      # 강조색 (황금)
CURRENT_COLOR = "#ff6b3d"      # 현재 구역 텍스트 색
NEXT_COLOR    = "#7fbbff"      # 다음 구역 텍스트 색
TIMER_COLOR   = "#c8ff70"      # 카운트다운 색
ERROR_COLOR   = "#ff4444"      # 오류 텍스트 색
DIM_COLOR     = "#888888"      # 보조 텍스트 색

FONT_TITLE    = ("Segoe UI", 9,  "bold")
FONT_LABEL    = ("Segoe UI", 8)
FONT_ZONE     = ("Segoe UI", 13, "bold")
FONT_NEXT     = ("Segoe UI", 10)
FONT_TIMER    = ("Consolas",  16, "bold")
FONT_ERROR    = ("Segoe UI", 8)

REFRESH_INTERVAL_SEC = 60   # API 재호출 간격 (초)


class OverlayApp(tk.Tk):
    """D2R 공포구역 오버레이 메인 앱."""

    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self._tz_info: Optional[TZInfo] = None
        self._drag_x = 0
        self._drag_y = 0
        self._fetch_thread: Optional[threading.Thread] = None
        self._is_fetching = False

        self._setup_window()
        self._build_ui()
        self._apply_config()

        # 첫 실행: 토큰이 없으면 설정창 팝업
        if not self.cfg.get("token_d2tz"):
            self.after(200, self._open_settings_required)
        else:
            self.after(300, self._refresh_data)

        # 카운트다운 루프 시작
        self._tick()

    # ─────────────────── 창 초기 설정 ──────────────────────────────────

    def _setup_window(self) -> None:
        """프레임리스 투명 창 설정."""
        self.overrideredirect(True)          # 타이틀바 제거
        self.wm_attributes("-topmost", self.cfg.get("always_on_top", True))
        self.wm_attributes("-alpha", self.cfg.get("alpha", 0.85))
        self.configure(bg=BG_COLOR)
        self.resizable(False, False)

        # 창 위치 복원
        x = self.cfg.get("x", 100)
        y = self.cfg.get("y", 100)
        self.geometry(f"+{x}+{y}")

    # ─────────────────── UI 빌드 ────────────────────────────────────────

    def _build_ui(self) -> None:
        """위젯 배치."""
        outer = tk.Frame(self, bg=BG_COLOR, bd=0)
        outer.pack(padx=0, pady=0)

        # 테두리 효과용 프레임
        border = tk.Frame(outer, bg=ACCENT_COLOR, bd=0)
        border.pack(padx=1, pady=1)

        inner = tk.Frame(border, bg=BG_COLOR, padx=14, pady=10)
        inner.pack()

        # ── 상단 타이틀 바 ────────────────────────────────────────────
        title_bar = tk.Frame(inner, bg=BG_COLOR)
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        self._title_label = tk.Label(
            title_bar, text="🔥 D2R 공포구역", bg=BG_COLOR, fg=ACCENT_COLOR,
            font=FONT_TITLE, anchor="w",
        )
        self._title_label.pack(side="left")

        # 닫기 버튼 (우측)
        close_btn = tk.Label(
            title_bar, text=" ✕ ", bg=BG_COLOR, fg=DIM_COLOR,
            font=("Segoe UI", 9), cursor="hand2",
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda _: self._quit())
        close_btn.bind("<Enter>", lambda _: close_btn.configure(fg="#ff4444"))
        close_btn.bind("<Leave>", lambda _: close_btn.configure(fg=DIM_COLOR))

        # ── 현재 구역 ─────────────────────────────────────────────────
        tk.Label(
            inner, text="현재 공포구역", bg=BG_COLOR, fg=DIM_COLOR, font=FONT_LABEL
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self._current_zone_label = tk.Label(
            inner, text="로딩 중...", bg=BG_COLOR, fg=CURRENT_COLOR,
            font=FONT_ZONE, anchor="w",
        )
        self._current_zone_label.grid(row=2, column=0, columnspan=2, sticky="w")

        self._current_act_label = tk.Label(
            inner, text="", bg=BG_COLOR, fg=DIM_COLOR, font=FONT_LABEL, anchor="w",
        )
        self._current_act_label.grid(row=3, column=0, columnspan=2, sticky="w")

        # ── 구분선 ────────────────────────────────────────────────────
        separator = tk.Frame(inner, bg="#333344", height=1)
        separator.grid(row=4, column=0, columnspan=2, sticky="ew", pady=6)

        # ── 다음 구역 + 카운트다운 ────────────────────────────────────
        next_frame = tk.Frame(inner, bg=BG_COLOR)
        next_frame.grid(row=5, column=0, columnspan=2, sticky="ew")

        next_info = tk.Frame(next_frame, bg=BG_COLOR)
        next_info.pack(side="left")

        tk.Label(
            next_info, text="다음 공포구역", bg=BG_COLOR, fg=DIM_COLOR, font=FONT_LABEL, anchor="w",
        ).pack(anchor="w")

        self._next_zone_label = tk.Label(
            next_info, text="-", bg=BG_COLOR, fg=NEXT_COLOR,
            font=FONT_NEXT, anchor="w",
        )
        self._next_zone_label.pack(anchor="w")

        # 카운트다운 (우측)
        timer_frame = tk.Frame(next_frame, bg=BG_COLOR)
        timer_frame.pack(side="right", padx=(20, 0))

        tk.Label(
            timer_frame, text="갱신까지", bg=BG_COLOR, fg=DIM_COLOR, font=FONT_LABEL,
        ).pack()
        self._timer_label = tk.Label(
            timer_frame, text="--:--", bg=BG_COLOR, fg=TIMER_COLOR, font=FONT_TIMER,
        )
        self._timer_label.pack()

        # ── 오류 메시지 ───────────────────────────────────────────────
        self._error_label = tk.Label(
            inner, text="", bg=BG_COLOR, fg=ERROR_COLOR,
            font=FONT_ERROR, anchor="w", justify="left", wraplength=260,
        )
        self._error_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # ── 드래그 이벤트 바인딩 ──────────────────────────────────────
        for widget in (self, outer, border, inner, title_bar, self._title_label):
            widget.bind("<ButtonPress-1>",   self._on_drag_start)
            widget.bind("<B1-Motion>",       self._on_drag_motion)

        # ── 우클릭 메뉴 ───────────────────────────────────────────────
        self._context_menu = tk.Menu(self, tearoff=0, bg="#1a1a2e", fg="#e0e0e0",
                                      activebackground="#f5a623", activeforeground="#000")
        self._context_menu.add_command(label="⚙  설정", command=self._open_settings)
        self._context_menu.add_command(label="🔄 새로 고침", command=self._refresh_data)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="❌ 종료", command=self._quit)

        self.bind("<Button-3>", self._show_context_menu)
        for widget in (outer, border, inner):
            widget.bind("<Button-3>", self._show_context_menu)

    # ─────────────────── 설정 적용 ──────────────────────────────────────

    def _apply_config(self) -> None:
        """현재 cfg를 창에 반영."""
        self.wm_attributes("-topmost", self.cfg.get("always_on_top", True))
        self.wm_attributes("-alpha", self.cfg.get("alpha", 0.85))

    # ─────────────────── 드래그 이동 ────────────────────────────────────

    def _on_drag_start(self, event: tk.Event) -> None:
        if self.cfg.get("lock_position", False):
            return
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag_motion(self, event: tk.Event) -> None:
        if self.cfg.get("lock_position", False):
            return
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ─────────────────── 우클릭 메뉴 ────────────────────────────────────

    def _show_context_menu(self, event: tk.Event) -> None:
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    # ─────────────────── 설정 창 ────────────────────────────────────────

    def _open_settings(self) -> None:
        SettingsDialog(self, self.cfg, on_save=self._on_settings_saved, require_token=False)

    def _open_settings_required(self) -> None:
        SettingsDialog(self, self.cfg, on_save=self._on_settings_saved, require_token=True)

    def _on_settings_saved(self, new_cfg: dict) -> None:
        """설정 저장 후 처리."""
        self.cfg = new_cfg
        save_config(self.cfg)
        self._apply_config()
        self._update_display_language()
        self._refresh_data()

    def _update_display_language(self) -> None:
        """언어 설정 변경 시 현재 데이터를 재표시."""
        if self._tz_info and not self._tz_info.error:
            self._show_tz_info(self._tz_info)

    # ─────────────────── API 데이터 갱신 ────────────────────────────────

    def _refresh_data(self) -> None:
        """백그라운드 스레드에서 API를 호출합니다."""
        if self._is_fetching:
            return
        self._is_fetching = True
        self._current_zone_label.configure(text="갱신 중...", fg=DIM_COLOR)
        self._error_label.configure(text="")

        token = self.cfg.get("token_d2tz", "")

        def _do_fetch():
            info = fetch_terror_zone(token)
            self.after(0, lambda: self._on_fetch_done(info))

        self._fetch_thread = threading.Thread(target=_do_fetch, daemon=True)
        self._fetch_thread.start()

    def _on_fetch_done(self, info: TZInfo) -> None:
        """API 호출 완료 후 UI 업데이트 (메인 스레드에서 실행)."""
        self._is_fetching = False
        self._tz_info = info
        if info.error:
            self._current_zone_label.configure(text="오류", fg=ERROR_COLOR)
            self._next_zone_label.configure(text="-")
            self._error_label.configure(text=info.error)
        else:
            self._show_tz_info(info)

    def _show_tz_info(self, info: TZInfo) -> None:
        lang = self.cfg.get("language", "ko")
        cur = get_display_name(info.current_zone, lang)
        nxt = get_display_name(info.next_zone, lang)
        act = get_act(info.current_zone)
        act_text = f"Act {act}" if act else ""

        self._current_zone_label.configure(text=cur, fg=CURRENT_COLOR)
        self._current_act_label.configure(text=act_text)
        self._next_zone_label.configure(text=nxt or "-")
        self._error_label.configure(text="")

    # ─────────────────── 카운트다운 타이머 ──────────────────────────────

    def _tick(self) -> None:
        """1초마다 카운트다운 업데이트 및 자동 갱신 트리거."""
        if self._tz_info and not self._tz_info.error:
            remaining = self._tz_info.seconds_until_update()
            mm = remaining // 60
            ss = remaining % 60
            self._timer_label.configure(text=f"{mm:02d}:{ss:02d}", fg=TIMER_COLOR)

            # 정각 도달 시 자동 갱신
            if remaining <= 0:
                self._refresh_data()
        elif not self._tz_info:
            self._timer_label.configure(text="--:--")
        # 오류 상태에서는 1분마다 재시도
        elif self._tz_info and self._tz_info.error:
            # 간단히: 타이머 표시 없이 60초 후 재시도
            pass

        self.after(1000, self._tick)

    # ─────────────────── 종료 ───────────────────────────────────────────

    def _quit(self) -> None:
        """종료 전 위치 저장."""
        self.cfg["x"] = self.winfo_x()
        self.cfg["y"] = self.winfo_y()
        save_config(self.cfg)
        self.destroy()
