"""Run the RetroBox desktop launcher."""

from __future__ import annotations

import argparse
import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from retrobox.launcher import (
    build_command,
    discover_games,
    find_core,
    find_retroarch,
    load_config,
)


class RetroBoxApp:
    """A small keyboard-friendly frontend for installed RetroArch cores."""

    def __init__(self, root: tk.Tk, config: dict[str, Any]) -> None:
        self.root = root
        self.config = config
        self.systems = config["systems"]
        self.selected_system = self.systems[0]
        self.games: list[Path] = []
        self.process: subprocess.Popen[bytes] | None = None

        self.root.title("RetroBox")
        self.root.geometry("980x640")
        self.root.minsize(720, 480)
        self.root.configure(bg="#10131c")
        self._configure_styles()
        self._build_layout()
        self._show_system(self.selected_system)
        self.root.after(500, self._check_process)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#10131c")
        style.configure("Panel.TFrame", background="#191e2b")
        style.configure(
            "TLabel", background="#10131c", foreground="#f3f4f8", font=("TkDefaultFont", 11)
        )
        style.configure(
            "Title.TLabel", font=("TkDefaultFont", 25, "bold"), foreground="#f5c451"
        )
        style.configure(
            "Subtle.TLabel", foreground="#aab2c5", font=("TkDefaultFont", 10)
        )
        style.configure(
            "System.TButton",
            background="#252c3b",
            foreground="#e9edf5",
            padding=(12, 10),
            anchor="w",
            font=("TkDefaultFont", 10),
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
            padding=(18, 11),
            font=("TkDefaultFont", 11, "bold"),
        )
        style.map("Launch.TButton", background=[("active", "#ffda78")])

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root, padding=(28, 22, 28, 14))
        header.pack(fill="x")
        ttk.Label(header, text="RETROBOX", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="YOUR CLASSICS. ONE LITTLE BOX.",
            style="Subtle.TLabel",
        ).pack(side="left", padx=(16, 0), pady=(9, 0))

        body = ttk.Frame(self.root, padding=(28, 8, 28, 20))
        body.pack(fill="both", expand=True)
        systems_panel = ttk.Frame(body, style="Panel.TFrame", padding=14)
        systems_panel.pack(side="left", fill="y", padx=(0, 16))
        ttk.Label(systems_panel, text="SYSTEMS", style="Subtle.TLabel").pack(
            anchor="w", padx=4, pady=(2, 10)
        )
        for system in self.systems:
            ttk.Button(
                systems_panel,
                text=system["name"],
                style="System.TButton",
                command=lambda selected=system: self._show_system(selected),
            ).pack(fill="x", pady=3)

        games_panel = ttk.Frame(body, style="Panel.TFrame", padding=18)
        games_panel.pack(side="left", fill="both", expand=True)
        self.system_title = ttk.Label(games_panel, text="", style="Title.TLabel")
        self.system_title.configure(font=("TkDefaultFont", 18, "bold"))
        self.system_title.pack(anchor="w")
        self.folder_label = ttk.Label(games_panel, text="", style="Subtle.TLabel")
        self.folder_label.pack(anchor="w", pady=(4, 14))

        list_frame = ttk.Frame(games_panel, style="Panel.TFrame", padding=8)
        list_frame.pack(fill="both", expand=True)
        self.game_list = tk.Listbox(
            list_frame,
            bg="#111621",
            fg="#f3f4f8",
            selectbackground="#f5c451",
            selectforeground="#17191f",
            activestyle="none",
            font=("TkFixedFont", 12),
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
        footer.pack(fill="x", pady=(14, 0))
        self.status_label = ttk.Label(footer, text="", style="Subtle.TLabel")
        self.status_label.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ttk.Button(
            footer, text="PLAY GAME", style="Launch.TButton", command=self._launch_selected
        ).pack(side="right")

        ttk.Label(
            self.root,
            text="↑ / ↓ select  •  Enter or double-click to play  •  Add your own ROMs to the listed folders",
            style="Subtle.TLabel",
        ).pack(anchor="w", padx=30, pady=(0, 14))

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

    def _check_process(self) -> None:
        if self.process is not None and self.process.poll() is not None:
            self.status_label.configure(text="Game closed. Choose another whenever you're ready.")
            self.process = None
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
