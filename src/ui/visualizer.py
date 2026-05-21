from __future__ import annotations

import re
import tkinter as tk
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk

from core.tree import MORSE_TREE, MorseNode, walk_path


class MorseTreeVisualizer(ctk.CTkFrame):
	def __init__(self, master: tk.Misc, width: int = 420, height: int = 520) -> None:
		super().__init__(master)
		self.canvas = tk.Canvas(self, width=width, height=height, bg="#12161c", highlightthickness=0)
		self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

		self.node_items: Dict[int, int] = {}
		self.text_items: Dict[int, int] = {}
		self.edge_items: Dict[Tuple[int, int], int] = {}
		self.node_positions: Dict[int, Tuple[float, float]] = {}
		self._max_depth = 0
		self._pending_resize: Optional[str] = None
		self._animation_id: Optional[str] = None

		self.default_node_fill = "#1f2630"
		self.default_node_outline = "#4d5b6b"
		self.default_edge = "#2f3a46"
		self.active_fill = "#00e5ff"
		self.active_edge = "#00e5ff"
		self.visited_fill = "#2b3340"
		self.final_fill = "#44d17a"

		self._nodes = self._collect_nodes(MORSE_TREE)
		self._draw_tree(width, height)
		self.canvas.bind("<Configure>", self._on_resize)

	def _on_resize(self, event: tk.Event) -> None:
		if event.width < 100 or event.height < 100:
			return
		if self._pending_resize is not None:
			self.after_cancel(self._pending_resize)
		self._pending_resize = self.after(60, lambda: self._draw_tree(event.width, event.height))

	def _collect_nodes(self, root: MorseNode) -> List[Tuple[MorseNode, int, int]]:
		nodes: List[Tuple[MorseNode, int, int]] = []
		stack: List[Tuple[MorseNode, int, int]] = [(root, 0, 1)]
		max_depth = 0
		while stack:
			node, depth, index = stack.pop()
			nodes.append((node, depth, index))
			max_depth = max(max_depth, depth)
			if node.dash is not None:
				stack.append((node.dash, depth + 1, index * 2 + 1))
			if node.dot is not None:
				stack.append((node.dot, depth + 1, index * 2))
		self._max_depth = max_depth
		return nodes

	def _position(self, depth: int, index: int, width: int, height: int) -> Tuple[float, float]:
		pad_x = 24
		pad_y = 24
		levels = max(1, self._max_depth)
		level_gap = max(60, (height - pad_y * 2) / levels)
		nodes_in_level = 2**depth
		index_in_level = index - nodes_in_level
		if nodes_in_level == 1:
			x = width / 2
		else:
			span = max(1, width - pad_x * 2)
			x = pad_x + index_in_level * (span / (nodes_in_level - 1))
		y = pad_y + depth * level_gap
		return x, y

	def _draw_tree(self, width: int, height: int) -> None:
		self.canvas.delete("all")
		self.node_items.clear()
		self.text_items.clear()
		self.edge_items.clear()
		self.node_positions.clear()

		for node, depth, index in self._nodes:
			x, y = self._position(depth, index, width, height)
			self.node_positions[id(node)] = (x, y)

		for node, _, _ in self._nodes:
			parent_id = id(node)
			parent_pos = self.node_positions.get(parent_id)
			if parent_pos is None:
				continue
			for child in (node.dot, node.dash):
				if child is None:
					continue
				child_pos = self.node_positions.get(id(child))
				if child_pos is None:
					continue
				edge_id = self.canvas.create_line(
					parent_pos[0],
					parent_pos[1],
					child_pos[0],
					child_pos[1],
					fill=self.default_edge,
					width=1,
				)
				self.edge_items[(parent_id, id(child))] = edge_id

		radius = 14
		for node, _, _ in self._nodes:
			node_id = id(node)
			x, y = self.node_positions[node_id]
			circle_id = self.canvas.create_oval(
				x - radius,
				y - radius,
				x + radius,
				y + radius,
				fill=self.default_node_fill,
				outline=self.default_node_outline,
				width=1,
			)
			label = node.char if node.char else ""
			text_id = self.canvas.create_text(
				x,
				y,
				text=label,
				fill="#e0e6ed",
				font=("Consolas", 10),
			)
			self.node_items[node_id] = circle_id
			self.text_items[node_id] = text_id

	def reset(self) -> None:
		for circle_id in self.node_items.values():
			self.canvas.itemconfig(circle_id, fill=self.default_node_fill, outline=self.default_node_outline)
		for edge_id in self.edge_items.values():
			self.canvas.itemconfig(edge_id, fill=self.default_edge, width=1)
		if self._animation_id is not None:
			self.after_cancel(self._animation_id)
			self._animation_id = None

	def highlight_path(self, node_path: List[MorseNode], delay_ms: int = 350) -> None:
		self.reset()
		path_ids = [id(node) for node in node_path if id(node) in self.node_items]
		if not path_ids:
			return

		def step(index: int) -> None:
			if index >= len(path_ids):
				return
			current_id = path_ids[index]
			current_circle = self.node_items[current_id]
			if index > 0:
				prev_id = path_ids[index - 1]
				prev_circle = self.node_items[prev_id]
				self.canvas.itemconfig(prev_circle, fill=self.visited_fill, outline=self.default_node_outline)
				edge_id = self.edge_items.get((prev_id, current_id))
				if edge_id is not None:
					self.canvas.itemconfig(edge_id, fill=self.active_edge, width=2)
			self.canvas.itemconfig(current_circle, fill=self.active_fill, outline=self.default_node_outline)
			if index == len(path_ids) - 1:
				self.canvas.itemconfig(current_circle, fill=self.final_fill, outline=self.default_node_outline)
				return
			self._animation_id = self.after(delay_ms, lambda: step(index + 1))

		step(0)

	def animate_morse(self, morse: str, unit_seconds: float) -> None:
		self.reset()
		min_unit_ms = 1 if unit_seconds <= 0 else 10
		steps = self._build_steps(morse, unit_seconds, min_unit_ms=min_unit_ms)
		if not steps:
			return
		self._run_steps(0, steps)

	def _build_steps(
		self,
		morse: str,
		unit_seconds: float,
		min_unit_ms: int = 10,
	) -> List[Tuple[str, Tuple[int, int, bool], int]]:
		unit_ms = max(min_unit_ms, int(unit_seconds * 1000))
		dot_ms = unit_ms
		dash_ms = unit_ms * 3
		intra_gap = unit_ms
		letter_gap = unit_ms * 3
		word_gap = unit_ms * 7

		steps: List[Tuple[str, Tuple[int, int, bool], int]] = []
		for token in self._tokenize_morse(morse):
			if token == "/":
				steps.append(("pause", (0, 0, False), word_gap))
				continue
			_, nodes = walk_path(MORSE_TREE, token)
			if len(nodes) < 2:
				continue
			steps.append(("reset", (0, 0, False), 1))
			prev_id = id(nodes[0])
			path_len = min(len(token), len(nodes) - 1)
			for index in range(path_len):
				symbol = token[index]
				if symbol not in (".", "-"):
					continue
				current_id = id(nodes[index + 1])
				is_final = index == path_len - 1
				duration = dot_ms if symbol == "." else dash_ms
				steps.append(("step", (prev_id, current_id, is_final), duration))
				prev_id = current_id
				if not is_final:
					steps.append(("pause", (0, 0, False), intra_gap))
			steps.append(("pause", (0, 0, False), letter_gap))
		return steps

	def _run_steps(self, index: int, steps: List[Tuple[str, Tuple[int, int, bool], int]]) -> None:
		if index >= len(steps):
			return
		action, payload, delay_ms = steps[index]
		if action == "reset":
			self.reset()
		elif action == "step":
			self._apply_step(payload)
		self._animation_id = self.after(max(1, delay_ms), lambda: self._run_steps(index + 1, steps))

	def _apply_step(self, payload: Tuple[int, int, bool]) -> None:
		prev_id, current_id, is_final = payload
		prev_circle = self.node_items.get(prev_id)
		current_circle = self.node_items.get(current_id)
		if prev_circle is not None:
			self.canvas.itemconfig(prev_circle, fill=self.visited_fill, outline=self.default_node_outline)
		edge_id = self.edge_items.get((prev_id, current_id))
		if edge_id is not None:
			self.canvas.itemconfig(edge_id, fill=self.active_edge, width=2)
		if current_circle is not None:
			fill = self.final_fill if is_final else self.active_fill
			self.canvas.itemconfig(current_circle, fill=fill, outline=self.default_node_outline)

	def _tokenize_morse(self, morse: str) -> List[str]:
		text = morse.strip()
		if not text:
			return []
		text = re.sub(r"\s{3,}", " / ", text)
		text = text.replace("/", " / ")
		return [token for token in text.split() if token]
