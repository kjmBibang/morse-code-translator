from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable

import customtkinter as ctk
import tkinter as tk

DATABASE_PATH = Path.cwd() / "history.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL,
            input TEXT NOT NULL,
            output TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def fetch_history(limit: int = 100) -> list[tuple[int, str, str, str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, mode, input, output, created_at FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows


def get_last_history_entry() -> tuple[str, str, str] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT mode, input, output FROM history ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row if row else None


def save_history(mode: str, input_text: str, output_text: str) -> None:
    last_entry = get_last_history_entry()
    if last_entry == (mode, input_text, output_text):
        return
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO history (mode, input, output) VALUES (?, ?, ?)",
            (mode, input_text, output_text),
        )
        conn.commit()


def delete_history(entry_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
        conn.commit()


def delete_all_history() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM history")
        conn.commit()


class HistoryWindow(ctk.CTkToplevel): 
    pass
    
    def __init__(
        self,
        master: tk.Tk | tk.Toplevel | None = None,
        on_use: Callable[[str, str, str], None] | None = None,
    ) -> None:
        super().__init__(master=master)
        self._on_use = on_use

        if master is not None and isinstance(master, (tk.Tk, tk.Toplevel)):
            self.transient(master)
        self.attributes("-topmost", True)
        self.title("History")
        self.geometry("760x520")
        self.minsize(600, 420)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_frame, text="History", font=("Arial", 16, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(
            header_frame,
            text="Delete All",
            fg_color="#8B0000",
            hover_color="#6B0000",
            width=100,
            command=self._delete_all,
        ).grid(row=0, column=1, sticky="e", padx=(0, 6))
        ctk.CTkButton(
            header_frame,
            text="Refresh",
            width=90,
            command=self._refresh_history,
        ).grid(row=0, column=2, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.history_frame.grid_columnconfigure(0, weight=1)

        self._refresh_history()


    def _refresh_history(self) -> None:
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        history_rows = fetch_history()
        if not history_rows:
            ctk.CTkLabel(
                self.history_frame,
                text="No history recorded yet.",
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
            return

        for row_index, (entry_id, mode, input_text, output_text, created_at) in enumerate(history_rows):
            self._build_card(row_index, entry_id, mode, input_text, output_text, created_at)

    def _build_card(
        self,
        row_index: int,
        entry_id: int,
        mode: str,
        input_text: str,
        output_text: str,
        created_at: str,
    ) -> None:
        card = ctk.CTkFrame(self.history_frame)
        card.grid(row=row_index, column=0, sticky="ew", padx=10, pady=8)
        card.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row,
            text=f"#{entry_id}  ·  {mode.title()}  ·  {created_at}",
            anchor="w",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(title_row, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_frame,
            text="Use",
            width=60,
            command=lambda m=mode, i=input_text, o=output_text: self._on_use_clicked(m, i, o),
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            btn_frame,
            text="Delete",
            width=70,
            fg_color="#8B0000",
            hover_color="#6B0000",
            command=lambda eid=entry_id: self._delete_entry(eid),
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            card,
            text=f"Input:   {input_text}",
            wraplength=680,
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        ctk.CTkLabel(
            card,
            text=f"Output: {output_text}",
            wraplength=680,
            anchor="w",
            justify="left",
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 10))

    def _on_use_clicked(self, mode: str, input_text: str, output_text: str) -> None:
        if self._on_use:
            self._on_use(mode, input_text, output_text)
        self.withdraw()   

    def _delete_entry(self, entry_id: int) -> None:
        delete_history(entry_id)
        self._refresh_history()

    def _delete_all(self) -> None:
        delete_all_history()
        self._refresh_history()