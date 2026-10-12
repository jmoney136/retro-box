"""Run the RetroBox desktop launcher."""

from __future__ import annotations

import argparse
import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from retrobox.controller import LinuxGamepad
from retrobox.launcher import (
    build_command,
    discover_games,
    find_core,
    find_retroarch,
    load_config,
)


def screen_scale(screen_width: int, screen_height: int) -> float:
    """Scale the launcher UI to a readable size on the current display."""
    return max(0.8, min(1.6, screen_width / 980, screen_height / 640))


class RetroBoxApp:
    """A small keyboard-friendly frontend for installed RetroArch cores."""

    def __init__(self, root: tk.Tk, config: dict[str, Any]) -> None:
        self.root = root
        self.config = config
        self.systems = config["systems"]
        self.selected_system = self.systems[0]
        self.games: list[Path] = []
        self.process: subprocess.Popen[bytes] | None = None
        self.gamepad = LinuxGamepad()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.ui_scale = screen_scale(self.screen_width, self.screen_height)
        self.fullscreen = True

        self.root.title("RetroBox")
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.minsize(720, 480)
        self.root.configure(bg="#10131c")
        self.root.attributes("-fullscreen", self.fullscreen)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self._configure_styles()
        self._build_layout()
        self._show_system(self.selected_system)
        self.root.after(500, self._check_process)
        self.root.after(100, self._poll_gamepad)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _scaled(self, value: int) -> int:
        return max(1, round(value * self.ui_scale))

    def _toggle_fullscreen(self, _event: tk.Event | None = None) -> str:
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        if self.fullscreen:
            self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        else:
            width = min(self._scaled(980), self.screen_width)
            height = min(self._scaled(640), self.screen_height)
            self.root.geometry(f"{width}x{height}+0+0")
        return "break"

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#10131c")
        style.configure("Panel.TFrame", background="#191e2b")
        style.configure(
            "TLabel",
            background="#10131c",
            foreground="#f3f4f8",
            font=("TkDefaultFont", self._scaled(11)),
        )
        style.configure(
            "Title.TLabel",
            font=("TkDefaultFont", self._scaled(25), "bold"),
            foreground="#f5c451",
        )
        style.configure(
            "Subtle.TLabel",
            foreground="#aab2c5",
            font=("TkDefaultFont", self._scaled(10)),
        )
        style.configure(
            "System.TButton",
            background="#252c3b",
            foreground="#e9edf5",
            padding=(self._scaled(12), self._scaled(10)),
            anchor="w",
            font=("TkDefaultFont", self._scaled(10)),
        )
        style.map(
            "System.TButton",
            background=[("active", "#35415a"), ("pressed", "#f5c451")],
            foreground=[("pressed", "#10131c")],
        )
        style.configure(
            "Launch.TButton",
            background="#f5c451",
            foreground="#17191f",
            padding=(self._scaled(18), self._scaled(11)),
            font=("TkDefaultFont", self._scaled(11), "bold"),
        )
        style.map("Launch.TButton", background=[("active", "#ffda78")])

    def _build_layout(self) -> None:
        scale = self._scaled
        header = ttk.Frame(
            self.root,
            padding=(scale(28), scale(22), scale(28), scale(14)),
        )
        header.pack(fill="x")
        ttk.Label(header, text="RETROBOX", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="YOUR CLASSICS. ONE LITTLE BOX.",
            style="Subtle.TLabel",
        ).pack(side="left", padx=(scale(16), 0), pady=(scale(9), 0))

        body = ttk.Frame(
            self.root,
            padding=(scale(28), scale(8), scale(28), scale(20)),
        )
        body.pack(fill="both", expand=True)
        systems_panel = ttk.Frame(body, style="Panel.TFrame", padding=scale(14))
        systems_panel.pack(side="left", fill="y", padx=(0, scale(16)))
        ttk.Label(systems_panel, text="SYSTEMS", style="Subtle.TLabel").pack(
            anchor="w", padx=scale(4), pady=(scale(2), scale(10))
        )
        for system in self.systems:
            ttk.Button(
                systems_panel,
                text=system["name"],
                style="System.TButton",
                command=lambda selected=system: self._show_system(selected),
            ).pack(fill="x", pady=scale(3))

        games_panel = ttk.Frame(body, style="Panel.TFrame", padding=scale(18))
        games_panel.pack(side="left", fill="both", expand=True)
        self.system_title = ttk.Label(games_panel, text="", style="Title.TLabel")
        self.system_title.configure(font=("TkDefaultFont", scale(18), "bold"))
        self.system_title.pack(anchor="w")
        self.folder_label = ttk.Label(games_panel, text="", style="Subtle.TLabel")
        self.folder_label.pack(anchor="w", pady=(scale(4), scale(14)))

        list_frame = ttk.Frame(games_panel, style="Panel.TFrame", padding=scale(8))
        list_frame.pack(fill="both", expand=True)
        self.game_list = tk.Listbox(
            list_frame,
            bg="#111621",
            fg="#f3f4f8",
            selectbackground="#f5c451",
            selectforeground="#17191f",
            activestyle="none",
            font=("TkFixedFont", scale(12)),
            borderwidth=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.game_list.yview)
        self.game_list.configure(yscrollcommand=scrollbar.set)
        self.game_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.game_list.bind("<Double-Button-1>", lambda _event: self._launch_selected())
        self.game_list.bind("<Return>", lambda _event: self._launch_selected())

        footer = ttk.Frame(games_panel, style="Panel.TFrame")
        footer.pack(fill="x", pady=(scale(14), 0))
        self.status_label = ttk.Label(footer, text="", style="Subtle.TLabel")
        self.status_label.pack(side="left", fill="x", expand=True, padx=(0, scale(12)))
        ttk.Button(
            footer, text="PLAY GAME", style="Launch.TButton", command=self._launch_selected
        ).pack(side="right")

        ttk.Label(
            self.root,
            text="↑ / ↓ select  •  Enter to play  •  Xbox: D-pad/stick navigate, A select, left/right change system",
            style="Subtle.TLabel",
        ).pack(anchor="w", padx=scale(30), pady=(0, scale(14)))

    def _show_system(self, system: dict[str, Any]) -> None:
        self.selected_system = system
        self.games = discover_games(system)
        self.system_title.configure(text=system["name"])
        self.folder_label.configure(text=str(Path(system["folder"]).expanduser()))
        self.game_list.delete(0, tk.END)
        for game in self.games:
            self.game_list.insert(tk.END, game.name)
        if self.games:
            self.game_list.selection_set(0)
            self.status_label.configure(text=f"{len(self.games)} game(s) found")
        else:
            self.status_label.configure(text="No games found — add ROM files to this folder.")

    def _launch_selected(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.status_label.configure(text="A game is already running.")
            return
        selection = self.game_list.curselection()
        if not selection:
            self.status_label.configure(text="Select a game first.")
            return

        retroarch = find_retroarch(self.config.get("retroarch", "retroarch"))
        if retroarch is None:
            messagebox.showerror(
                "RetroArch not found",
                "Install RetroArch, then check the 'retroarch' setting in retrobox/systems.json.",
            )
            return

        core = find_core(self.selected_system["core"], self.config.get("core_directories", []))
        if core is None:
            messagebox.showerror(
                "Core not found",
                f"Could not find {self.selected_system['core']}. Install that libretro core or "
                "add its directory to 'core_directories' in retrobox/systems.json.",
            )
            return

        game = self.games[selection[0]]
        command = build_command(retroarch, core, game)
        try:
            self.process = subprocess.Popen(command)
        except OSError as error:
            messagebox.showerror("Could not launch game", str(error))
            return
        self.status_label.configure(text=f"Playing {game.name}…")
        self.root.withdraw()

    def _move_game_selection(self, offset: int) -> None:
        if not self.games:
            return
        selection = self.game_list.curselection()
        index = selection[0] if selection else 0
        index = max(0, min(len(self.games) - 1, index + offset))
        self.game_list.selection_clear(0, tk.END)
        self.game_list.selection_set(index)
        self.game_list.activate(index)
        self.game_list.see(index)

    def _change_system(self, offset: int) -> None:
        current = next(
            (index for index, system in enumerate(self.systems) if system["id"] == self.selected_system["id"]),
            0,
        )
        self._show_system(self.systems[(current + offset) % len(self.systems)])

    def _poll_gamepad(self) -> None:
        for action in self.gamepad.poll():
            if action == "up":
                self._move_game_selection(-1)
            elif action == "down":
                self._move_game_selection(1)
            elif action == "left":
                self._change_system(-1)
            elif action == "right":
                self._change_system(1)
            elif action == "select":
                self._launch_selected()
            elif action == "exit":
                self._exit_game()
        self.root.after(20 if self.gamepad.connected else 500, self._poll_gamepad)

    def _exit_game(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()

    def _close(self) -> None:
        self.gamepad.close()
        self.root.destroy()

    def _check_process(self) -> None:
        if self.process is not None and self.process.poll() is not None:
            self.process = None
            self._show_system(self.selected_system)
            self.status_label.configure(text="Game closed. Choose another whenever you're ready.")
            self.root.deiconify()
            self.root.attributes("-fullscreen", self.fullscreen)
            self.root.lift()
            self.root.focus_force()
            self.game_list.focus_set()
        self.root.after(500, self._check_process)


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch your legally obtained retro game ROMs.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("systems.json"),
        help="path to a RetroBox JSON configuration file",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(f"could not load config: {error}")

    root = tk.Tk()
    RetroBoxApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
