"""ROM discovery and RetroArch command helpers."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate the launcher configuration."""
    with config_path.expanduser().open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    if not isinstance(config.get("systems"), list):
        raise ValueError("Configuration must contain a 'systems' list.")
    if not config["systems"]:
        raise ValueError("Configuration must define at least one system.")
    return config


def discover_games(system: dict[str, Any]) -> list[Path]:
    """Return supported ROM files in a system's folder, sorted by name."""
    folder = Path(system["folder"]).expanduser()
    extensions = {extension.lower() for extension in system.get("extensions", [])}
    if not folder.is_dir():
        return []

    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        ),
        key=lambda path: path.name.casefold(),
    )


def find_core(core: str, core_directories: list[str]) -> Path | None:
    """Resolve a core path, accepting either an explicit path or a filename."""
    requested = Path(core).expanduser()
    if requested.is_absolute() or requested.parent != Path("."):
        return requested if requested.is_file() else None

    for directory in core_directories:
        candidate = Path(directory).expanduser() / core
        if candidate.is_file():
            return candidate
    return None


def find_retroarch(command: str) -> str | None:
    """Find the RetroArch executable configured by name or absolute path."""
    expanded = str(Path(command).expanduser()) if "~" in command else command
    if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
        return expanded
    return shutil.which(expanded)


def build_command(retroarch: str, core: Path, game: Path) -> list[str]:
    """Build a shell-free command line to launch one game."""
    return [retroarch, "--verbose", "--libretro", str(core), str(game)]
