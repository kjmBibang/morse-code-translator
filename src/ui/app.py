from __future__ import annotations

import time
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from audio.beeper import build_morse_wave, play_wave, sanitize_morse_symbols, stop_playback
from core import translate
from core.telegraph import TelegraphSession
from core.tree import MORSE_TABLE
from ui.visualizer import MorseTreeVisualizer
from ui.history import HistoryWindow, save_history


class MorseApp(ctk.CTk):
	def __init__(self) -> None:
		super().__init__()
		ctk.set_appearance_mode("dark")

		self.title("Morse Code Translator")
		self.geometry("1100x700")
		self.minsize(900, 600)
		self.after(50, lambda: self.state("zoomed"))

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		self.tabview = ctk.CTkTabview(self)
		self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

		self.encoder_tab = self.tabview.add("Encoder")
		self.decoder_tab = self.tabview.add("Decoder")
		self.telegraph_tab = self.tabview.add("Telegraph")
		self.audio_tab = self.tabview.add("Audio")

		self.telegraph_session = TelegraphSession()
		self._history_window: HistoryWindow | None = None

		self._build_encoder_tab()
		self._build_decoder_tab()
		self._build_telegraph_tab()
		self._build_placeholder_tab(self.audio_tab, "Audio tools coming soon.")
		self._build_menus()
# =============START====05-font-size======================
		self._apply_font_size()
# ==================END====================================		

		self.bind_all("<Left>", self._on_telegraph_dot, add="+")
		self.bind_all("<Right>", self._on_telegraph_dash, add="+")
		self.bind_all("<space>", self._on_telegraph_space, add="+")
		self.bind_all("<Return>", self._on_telegraph_commit, add="+")
		self._audio_playing = False
		self._active_play_button: Optional[ctk.CTkButton] = None
		self._playback_after_id: Optional[str] = None
		self._sync_play_buttons()

	def _build_encoder_tab(self) -> None:
		self.encoder_tab.grid_columnconfigure(0, weight=1)
		self.encoder_tab.grid_rowconfigure(0, weight=1)

		self.encoder_pane = tk.PanedWindow(
			self.encoder_tab,
			orient="horizontal",
			sashrelief="raised",
			bg="#12161c",
		)
		self.encoder_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

		left_frame = ctk.CTkFrame(self.encoder_pane, fg_color="transparent")
		left_frame.grid_columnconfigure(0, weight=1)
		left_frame.grid_rowconfigure(1, weight=1)
		left_frame.grid_rowconfigure(4, weight=1)

		self.encoder_side = ctk.CTkFrame(self.encoder_pane)
		self.encoder_side.grid_columnconfigure(0, weight=1)
		self.encoder_side.grid_rowconfigure(0, weight=1)
		self.encoder_side_inner = ctk.CTkScrollableFrame(self.encoder_side)
		self.encoder_side_inner.grid(row=0, column=0, sticky="nsew")
		self.encoder_side_inner.grid_columnconfigure(0, weight=1)
		self.encoder_side_inner.grid_rowconfigure(0, weight=1)
		self.encoder_side_inner.grid_rowconfigure(1, weight=1)

		self.encoder_pane.add(left_frame, minsize=420)
		self.encoder_pane.add(self.encoder_side, minsize=280)

		ctk.CTkLabel(left_frame, text="Text Input").grid(
			row=0, column=0, sticky="w", padx=10, pady=(10, 4)
		)
		self.encoder_input = ctk.CTkTextbox(left_frame, height=120)
		self.encoder_input.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

		encode_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
		encode_btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
		ctk.CTkButton(encode_btn_frame, text="Encode", command=self._on_encode).grid(row=0, column=0, sticky="w")
		ctk.CTkButton(encode_btn_frame, text="History", width=90, command=self._open_history).grid(row=0, column=1, sticky="w", padx=(8, 0))

		output_header = ctk.CTkFrame(left_frame, fg_color="transparent")
		output_header.grid(row=3, column=0, sticky="ew", padx=10, pady=(10, 4))
		output_header.grid_columnconfigure(0, weight=1)
		ctk.CTkLabel(output_header, text="Morse Output").grid(row=0, column=0, sticky="w")
		self.encoder_play_btn = ctk.CTkButton(
			output_header,
			text="Play",
			width=80,
			command=self._on_encoder_play,
		)
		self.encoder_play_btn.grid(row=0, column=1, sticky="e")
		self.encoder_output = ctk.CTkTextbox(left_frame, height=120)
		self.encoder_output.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
		self._set_text(self.encoder_output, "")

		self.encoder_visualizer = MorseTreeVisualizer(self.encoder_side_inner)
		self.encoder_visualizer.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))
		self.encoder_guide = self._build_morse_guide(self.encoder_side_inner)
		self.encoder_guide.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
		self.encoder_visualizer.grid_remove()
		self.encoder_guide.grid_remove()
		self.encoder_pane.forget(self.encoder_side)
		self.encoder_panels = [self.encoder_visualizer, self.encoder_guide]
		self.after(80, lambda: self._set_pane_ratio(self.encoder_pane, 0.6))

	def _build_decoder_tab(self) -> None:
		self.decoder_tab.grid_columnconfigure(0, weight=1)
		self.decoder_tab.grid_rowconfigure(0, weight=1)

		self.decoder_pane = tk.PanedWindow(
			self.decoder_tab,
			orient="horizontal",
			sashrelief="raised",
			bg="#12161c",
		)
		self.decoder_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

		left_frame = ctk.CTkFrame(self.decoder_pane, fg_color="transparent")
		left_frame.grid_columnconfigure(0, weight=1)
		left_frame.grid_rowconfigure(1, weight=1)
		left_frame.grid_rowconfigure(4, weight=1)

		self.decoder_side = ctk.CTkFrame(self.decoder_pane)
		self.decoder_side.grid_columnconfigure(0, weight=1)
		self.decoder_side.grid_rowconfigure(0, weight=1)
		self.decoder_side_inner = ctk.CTkScrollableFrame(self.decoder_side)
		self.decoder_side_inner.grid(row=0, column=0, sticky="nsew")
		self.decoder_side_inner.grid_columnconfigure(0, weight=1)
		self.decoder_side_inner.grid_rowconfigure(0, weight=1)
		self.decoder_side_inner.grid_rowconfigure(1, weight=1)

		self.decoder_pane.add(left_frame, minsize=420)
		self.decoder_pane.add(self.decoder_side, minsize=280)

		input_header = ctk.CTkFrame(left_frame, fg_color="transparent")
		input_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
		input_header.grid_columnconfigure(0, weight=1)
		ctk.CTkLabel(input_header, text="Morse Input").grid(row=0, column=0, sticky="w")
		self.decoder_play_btn = ctk.CTkButton(
			input_header,
			text="Play",
			width=80,
			command=self._on_decoder_play,
		)
		self.decoder_play_btn.grid(row=0, column=1, sticky="e")
		self.decoder_input = ctk.CTkTextbox(left_frame, height=120)
		self.decoder_input.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

		decode_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
		decode_btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
		ctk.CTkButton(decode_btn_frame, text="Decode", command=self._on_decode).grid(row=0, column=0, sticky="w")
		ctk.CTkButton(decode_btn_frame, text="History", width=90, command=self._open_history).grid(row=0, column=1, sticky="w", padx=(8, 0))

		ctk.CTkLabel(left_frame, text="Text Output").grid(
			row=3, column=0, sticky="w", padx=10, pady=(10, 4)
		)
		self.decoder_output = ctk.CTkTextbox(left_frame, height=120)
		self.decoder_output.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
		self._set_text(self.decoder_output, "")

		self.decoder_visualizer = MorseTreeVisualizer(self.decoder_side_inner)
		self.decoder_visualizer.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))
		self.decoder_guide = self._build_morse_guide(self.decoder_side_inner)
		self.decoder_guide.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
		self.decoder_visualizer.grid_remove()
		self.decoder_guide.grid_remove()
		self.decoder_pane.forget(self.decoder_side)
		self.decoder_panels = [self.decoder_visualizer, self.decoder_guide]
		self.after(80, lambda: self._set_pane_ratio(self.decoder_pane, 0.6))

	def _build_telegraph_tab(self) -> None:
		self.telegraph_tab.grid_columnconfigure(0, weight=1)
		self.telegraph_tab.grid_rowconfigure(0, weight=1)

		self.telegraph_pane = tk.PanedWindow(
			self.telegraph_tab,
			orient="horizontal",
			sashrelief="raised",
			bg="#12161c",
		)
		self.telegraph_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

		left_frame = ctk.CTkFrame(self.telegraph_pane, fg_color="transparent")
		left_frame.grid_columnconfigure(0, weight=1)
		left_frame.grid_rowconfigure(2, weight=1)
		left_frame.grid_rowconfigure(5, weight=1)

		self.telegraph_side = ctk.CTkFrame(self.telegraph_pane)
		self.telegraph_side.grid_columnconfigure(0, weight=1)
		self.telegraph_side.grid_rowconfigure(0, weight=1)
		self.telegraph_side_inner = ctk.CTkScrollableFrame(self.telegraph_side)
		self.telegraph_side_inner.grid(row=0, column=0, sticky="nsew")
		self.telegraph_side_inner.grid_columnconfigure(0, weight=1)

		self.telegraph_pane.add(left_frame, minsize=420)
		self.telegraph_pane.add(self.telegraph_side, minsize=280)

		ctk.CTkLabel(left_frame, text="Current Morse Symbols").grid(
			row=0, column=0, sticky="w", padx=10, pady=(10, 4)
		)
		ctk.CTkLabel(
			left_frame,
			text="Use Left/Right arrows for dot/dash, Space for word gap, Enter to commit.",
			text_color="#cccccc",
			wraplength=700,
		).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
		self.telegraph_symbols = ctk.CTkTextbox(left_frame, height=80)
		self.telegraph_symbols.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
		self._set_text(self.telegraph_symbols, "")

		button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
		button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
		button_frame.grid_columnconfigure(0, weight=1)
		button_frame.grid_columnconfigure(1, weight=1)
		button_frame.grid_columnconfigure(2, weight=1)
		button_frame.grid_columnconfigure(3, weight=1)
		button_frame.grid_columnconfigure(4, weight=1)
		button_frame.grid_columnconfigure(5, weight=1)
		ctk.CTkButton(button_frame, text="Left Arrow", command=self._on_telegraph_dot).grid(row=0, column=0, sticky="ew", padx=4)
		ctk.CTkButton(button_frame, text="Right Arrow", command=self._on_telegraph_dash).grid(row=0, column=1, sticky="ew", padx=4)
		ctk.CTkButton(button_frame, text="Commit", command=self._on_telegraph_commit).grid(row=0, column=2, sticky="ew", padx=4)
		ctk.CTkButton(button_frame, text="Space", command=self._on_telegraph_space).grid(row=0, column=3, sticky="ew", padx=4)
		ctk.CTkButton(button_frame, text="Reset", command=self._on_telegraph_reset).grid(row=0, column=4, sticky="ew", padx=4)
		ctk.CTkButton(button_frame, text="History", command=self._open_history).grid(row=0, column=5, sticky="ew", padx=4)

		ctk.CTkLabel(left_frame, text="Decoded Text").grid(
			row=4, column=0, sticky="w", padx=10, pady=(10, 4)
		)
		self.telegraph_output = ctk.CTkTextbox(left_frame, height=120)
		self.telegraph_output.grid(row=5, column=0, sticky="nsew", padx=10, pady=(0, 10))
		self._set_text(self.telegraph_output, "")

		self.telegraph_guide = self._build_morse_guide(self.telegraph_side_inner)
		self.telegraph_guide.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

		self._refresh_telegraph_state()

	def _refresh_telegraph_state(self) -> None:
		self._set_text(self.telegraph_symbols, self.telegraph_session.current_symbols)
		self._set_text(self.telegraph_output, self.telegraph_session.decoded_text)

	def _telegraph_active(self) -> bool:
		return self.tabview.get() == "Telegraph"

	def _on_telegraph_dot(self, event=None) -> str | None:
		if not self._telegraph_active():
			return None
		self.telegraph_session.add_dot()
		self._refresh_telegraph_state()
		return "break"

	def _on_telegraph_dash(self, event=None) -> str | None:
		if not self._telegraph_active():
			return None
		self.telegraph_session.add_dash()
		self._refresh_telegraph_state()
		return "break"

	def _on_telegraph_commit(self, event=None) -> str | None:
		if not self._telegraph_active():
			return None
		self.telegraph_session.commit_character()
		self._refresh_telegraph_state()
		return "break"

	def _on_telegraph_space(self, event=None) -> str | None:
		if not self._telegraph_active():
			return None
		self.telegraph_session.add_space()
		self._refresh_telegraph_state()
		return "break"

	def _open_history(self) -> None:
		"""Open (or re-raise) the history popup."""
		if self._history_window is not None and self._history_window.winfo_exists():
			self._history_window.deiconify()
			self._history_window.lift()
			self._history_window._refresh_history()
			return
		self._history_window = HistoryWindow(master=self, on_use=self._on_history_use)

	def _on_history_use(self, mode: str, input_text: str, output_text: str) -> None:
		"""Load a history entry's input into the right tab and switch to it."""
		if mode == "encode":
			self.tabview.set("Encoder")
			self.encoder_input.configure(state="normal")
			self.encoder_input.delete("1.0", "end")
			self.encoder_input.insert("1.0", input_text)
		elif mode == "decode":
			self.tabview.set("Decoder")
			self.decoder_input.configure(state="normal")
			self.decoder_input.delete("1.0", "end")
			self.decoder_input.insert("1.0", input_text)
		elif mode == "telegraph":
			self.tabview.set("Telegraph")
			self.telegraph_session.reset()
			# Telegraph input is morse symbols — pre-fill the decoded text field
			# so the user can see what was produced before; current_symbols stays clear.
			self.telegraph_session.decoded_text = output_text
			self._refresh_telegraph_state()
		# audio: reserved for future use

	def _on_telegraph_reset(self) -> None:
		decoded = self.telegraph_session.decoded_text
		symbols = self.telegraph_session.current_symbols
		if decoded or symbols:
			save_history("telegraph", symbols, decoded)
		self.telegraph_session.reset()
		self._refresh_telegraph_state()

	def _build_placeholder_tab(self, tab: ctk.CTkFrame, message: str) -> None:
		tab.grid_columnconfigure(0, weight=1)
		ctk.CTkLabel(tab, text=message).grid(row=0, column=0, padx=10, pady=10, sticky="w")

	def _build_menus(self) -> None:
		self.menu_bar = tk.Menu(self)
		file_menu = tk.Menu(self.menu_bar, tearoff=0)
		self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
		self.animation_menu = tk.Menu(self.menu_bar, tearoff=0)
		self.sound_menu = tk.Menu(self.menu_bar, tearoff=0)
		self.menu_bar.add_cascade(label="File", menu=file_menu)
		self.menu_bar.add_cascade(label="View", menu=self.view_menu)
		self.menu_bar.add_cascade(label="Animation", menu=self.animation_menu)
		self.menu_bar.add_cascade(label="Sound", menu=self.sound_menu)
		self.config(menu=self.menu_bar)

		file_menu.add_command(label="Exit", command=self.destroy)

		self.encoder_visual_var = tk.BooleanVar(value=False)
		self.encoder_guide_var = tk.BooleanVar(value=False)
		self.decoder_visual_var = tk.BooleanVar(value=False)
		self.decoder_guide_var = tk.BooleanVar(value=False)
		self.animation_speed_var = tk.StringVar(value="normal")
		self.sound_enabled_var = tk.BooleanVar(value=True)
		self.sound_volume_var = tk.IntVar(value=75)

		self.view_menu.add_checkbutton(
			label="Encoder: Visualizer",
			variable=self.encoder_visual_var,
			command=self._toggle_encoder_visual,
		)
		self.view_menu.add_checkbutton(
			label="Encoder: Guide",
			variable=self.encoder_guide_var,
			command=self._toggle_encoder_guide,
		)
		self.view_menu.add_separator()
		self.view_menu.add_checkbutton(
			label="Decoder: Visualizer",
			variable=self.decoder_visual_var,
			command=self._toggle_decoder_visual,
		)
		self.view_menu.add_checkbutton(
			label="Decoder: Guide",
			variable=self.decoder_guide_var,
			command=self._toggle_decoder_guide,
		)


# ======================START 05-font-size-option=================================
		self.font_size_var = tk.StringVar(value="normal")
		font_menu = tk.Menu(self.view_menu, tearoff=0)
		font_menu.add_radiobutton(label="Small", value="small", variable=self.font_size_var, command=self._apply_font_size)
		font_menu.add_radiobutton(label="Normal", value="normal", variable=self.font_size_var, command=self._apply_font_size)
		font_menu.add_radiobutton(label="Large", value="large", variable=self.font_size_var, command=self._apply_font_size)
		font_menu.add_radiobutton(label="Extra Large", value="xlarge", variable=self.font_size_var, command=self._apply_font_size)
		self.menu_bar.add_cascade(label="Font", menu=font_menu)
# ===============================END===============================================



		self.animation_menu.add_radiobutton(
			label="Slow",
			value="slow",
			variable=self.animation_speed_var,
		)
		self.animation_menu.add_radiobutton(
			label="Normal",
			value="normal",
			variable=self.animation_speed_var,
		)
		self.animation_menu.add_radiobutton(
			label="Fast",
			value="fast",
			variable=self.animation_speed_var,
		)
		self.animation_menu.add_separator()
		self.animation_menu.add_radiobutton(
			label="Real-time",
			value="realtime",
			variable=self.animation_speed_var,
		)

		self.sound_menu.add_checkbutton(
			label="Enable sound",
			variable=self.sound_enabled_var,
			command=self._on_sound_toggle,
		)
		self.sound_menu.add_separator()
		self.sound_menu.add_radiobutton(
			label="Volume 25%",
			value=25,
			variable=self.sound_volume_var,
		)
		self.sound_menu.add_radiobutton(
			label="Volume 50%",
			value=50,
			variable=self.sound_volume_var,
		)
		self.sound_menu.add_radiobutton(
			label="Volume 75%",
			value=75,
			variable=self.sound_volume_var,
		)
		self.sound_menu.add_radiobutton(
			label="Volume 100%",
			value=100,
			variable=self.sound_volume_var,
		)


	def _resolve_unit_seconds(self, elapsed_seconds: float, morse: str) -> float:
		mode = self.animation_speed_var.get()
		speed_map = {
			"slow": 0.6,
			"normal": 0.35,
			"fast": 0.18,
		}
		if mode == "realtime":
			symbols = sum(1 for ch in morse if ch in ".-")
			if symbols <= 0:
				return 0.08
			return max(0.02, elapsed_seconds / symbols)
		return speed_map.get(mode, 0.35)

	def _get_volume(self) -> float:
		if not self.sound_enabled_var.get():
			return 0.0
		return max(0.0, min(100.0, float(self.sound_volume_var.get()))) / 100.0

	def _on_sound_toggle(self) -> None:
		if not self.sound_enabled_var.get():
			self._stop_audio()

	def _stop_audio(self) -> None:
		stop_playback()
		if self._playback_after_id is not None:
			self.after_cancel(self._playback_after_id)
			self._playback_after_id = None
		if self._active_play_button is not None:
			self._active_play_button.configure(text="Play")
			self._active_play_button = None
		self._audio_playing = False

	def _play_morse_sequence(
		self,
		morse: str,
		unit_seconds: float,
		button: Optional[ctk.CTkButton],
		update_button: bool,
	) -> None:
		volume = self._get_volume()
		if volume <= 0:
			return
		cleaned = sanitize_morse_symbols(morse)
		if not cleaned:
			return
		wave, sample_rate = build_morse_wave(cleaned, unit_seconds, volume)
		if wave.size == 0:
			return
		self._stop_audio()
		play_wave(wave, sample_rate)
		if update_button and button is not None:
			button.configure(text="Pause")
			self._audio_playing = True
			self._active_play_button = button
			duration_ms = int(len(wave) / sample_rate * 1000)
			self._playback_after_id = self.after(duration_ms, self._stop_audio)

	def _toggle_playback(self, morse: str, button: ctk.CTkButton) -> None:
		if self._audio_playing:
			self._stop_audio()
			return
		self._play_morse_sequence(morse, 0.12, button, update_button=True)

	def _on_encoder_play(self) -> None:
		if self.encoder_visualizer.winfo_ismapped():
			return
		morse = self._get_text(self.encoder_output)
		self._toggle_playback(morse, self.encoder_play_btn)

	def _on_decoder_play(self) -> None:
		if self.decoder_visualizer.winfo_ismapped():
			return
		morse = self._get_text(self.decoder_input)
		self._toggle_playback(morse, self.decoder_play_btn)

	def _set_panel_visibility(
		self,
		pane: tk.PanedWindow,
		side_frame: ctk.CTkFrame,
		panel: ctk.CTkFrame,
		panels: list[ctk.CTkFrame],
		visible: bool,
	) -> None:
		if visible:
			self._ensure_side_pane(pane, side_frame, True)
			panel.grid()
		else:
			panel.grid_remove()

		self._sync_side_panel(pane, side_frame, panels, force_visible=visible)

	def _sync_side_panel(
		self,
		pane: tk.PanedWindow,
		side_frame: ctk.CTkFrame,
		panels: list[ctk.CTkFrame],
		force_visible: bool | None = None,
	) -> None:
		self.update_idletasks()
		any_visible = any(panel.winfo_ismapped() for panel in panels)
		if force_visible is True:
			any_visible = True
		self._ensure_side_pane(pane, side_frame, any_visible)

	def _sync_menu_var(self, var: tk.BooleanVar, panel: ctk.CTkFrame) -> None:
		self.after_idle(lambda: var.set(panel.winfo_ismapped()))
		self.after_idle(self._sync_play_buttons)

	def _sync_play_buttons(self) -> None:
		encoder_state = "disabled" if self.encoder_visualizer.winfo_ismapped() else "normal"
		decoder_state = "disabled" if self.decoder_visualizer.winfo_ismapped() else "normal"
		self.encoder_play_btn.configure(state=encoder_state)
		self.decoder_play_btn.configure(state=decoder_state)

	def _ensure_side_pane(self, pane: tk.PanedWindow, side_frame: ctk.CTkFrame, show: bool) -> None:
		panes = pane.panes()
		side_name = str(side_frame)
		if show and side_name not in panes:
			pane.add(side_frame, minsize=280)
			self.after(50, lambda: self._set_pane_ratio(pane, 0.6))
		elif not show and side_name in panes:
			pane.forget(side_frame)

	def _set_pane_ratio(self, pane: tk.PanedWindow, ratio: float) -> None:
		width = pane.winfo_width()
		if width < 2:
			self.after(60, lambda: self._set_pane_ratio(pane, ratio))
			return
		pane.sash_place(0, int(width * ratio), 0)

	def _toggle_encoder_visual(self) -> None:
		self._set_panel_visibility(
			self.encoder_pane,
			self.encoder_side,
			self.encoder_visualizer,
			self.encoder_panels,
			self.encoder_visual_var.get(),
		)
		self._sync_menu_var(self.encoder_visual_var, self.encoder_visualizer)
		if self.encoder_visualizer.winfo_ismapped():
			self._stop_audio()

	def _toggle_encoder_guide(self) -> None:
		self._set_panel_visibility(
			self.encoder_pane,
			self.encoder_side,
			self.encoder_guide,
			self.encoder_panels,
			self.encoder_guide_var.get(),
		)
		self._sync_menu_var(self.encoder_guide_var, self.encoder_guide)

	def _toggle_decoder_visual(self) -> None:
		self._set_panel_visibility(
			self.decoder_pane,
			self.decoder_side,
			self.decoder_visualizer,
			self.decoder_panels,
			self.decoder_visual_var.get(),
		)
		self._sync_menu_var(self.decoder_visual_var, self.decoder_visualizer)
		if self.decoder_visualizer.winfo_ismapped():
			self._stop_audio()

	def _toggle_decoder_guide(self) -> None:
		self._set_panel_visibility(
			self.decoder_pane,
			self.decoder_side,
			self.decoder_guide,
			self.decoder_panels,
			self.decoder_guide_var.get(),
		)
		self._sync_menu_var(self.decoder_guide_var, self.decoder_guide)

	def _build_morse_guide(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
		frame = ctk.CTkFrame(parent)
		frame.grid_columnconfigure(0, weight=1)
		frame.grid_rowconfigure(1, weight=1)
		ctk.CTkLabel(frame, text="Morse Guide").grid(
			row=0, column=0, sticky="w", padx=10, pady=(10, 4)
		)
		textbox = ctk.CTkTextbox(frame)
		textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
		textbox.insert("1.0", self._format_morse_guide())
		textbox.configure(state="disabled", font=("Consolas", 12))
		return frame

	def _format_morse_guide(self) -> str:
		entries = [f"{char} {code}" for char, code in MORSE_TABLE.items()]
		lines = []
		row = []
		for entry in entries:
			row.append(entry.ljust(10))
			if len(row) == 4:
				lines.append("  ".join(row).rstrip())
				row = []
		if row:
			lines.append("  ".join(row).rstrip())
		return "\n".join(lines)

	def _get_text(self, textbox: ctk.CTkTextbox) -> str:
		return textbox.get("1.0", "end").strip()

	def _set_text(self, textbox: ctk.CTkTextbox, text: str) -> None:
		textbox.configure(state="normal")
		textbox.delete("1.0", "end")
		textbox.insert("1.0", text)
		textbox.configure(state="disabled")

	def _on_encode(self) -> None:
		text = self._get_text(self.encoder_input)
		if not text:
			self._set_text(self.encoder_output, "Enter text to encode.")
			return
		start = time.perf_counter()
		result, _ = translate(text, "encode")
		elapsed = time.perf_counter() - start
		self._set_text(self.encoder_output, result)
		save_history("encode", text, result)
		if self.encoder_visualizer.winfo_ismapped():
			morse = sanitize_morse_symbols(result)
			unit_seconds = self._resolve_unit_seconds(elapsed, morse)
			self.encoder_visualizer.animate_morse(morse, unit_seconds)
			self._play_morse_sequence(morse, unit_seconds, None, False)

	def _on_decode(self) -> None:
		text = self._get_text(self.decoder_input)
		if not text:
			self._set_text(self.decoder_output, "Enter Morse to decode.")
			return
		start = time.perf_counter()
		result, _ = translate(text, "decode")
		elapsed = time.perf_counter() - start
		self._set_text(self.decoder_output, result)
		save_history("decode", text, result)
		if self.decoder_visualizer.winfo_ismapped():
			morse = sanitize_morse_symbols(text)
			unit_seconds = self._resolve_unit_seconds(elapsed, morse)
			self.decoder_visualizer.animate_morse(morse, unit_seconds)
			self._play_morse_sequence(morse, unit_seconds, None, False)

# ====================START 05-font-size-option=======================
	def _apply_font_size(self) -> None:
		"""Apply the selected font size across common widgets."""
		size_map = {
			"small": 14,
			"normal": 20,
			"large": 26,
			"xlarge": 32,
		}
		size = size_map.get(self.font_size_var.get(), 12)
		font = ("Consolas", size)

		def _recurse_config(w):
			try:
				w.configure(font=font)
			except Exception:
				pass
			for child in w.winfo_children():
				_recurse_config(child)

		_recurse_config(self)

#===================END=============================
def run() -> None:
	app = MorseApp()
	app.mainloop()
