import json
import tempfile
import unittest
from pathlib import Path

from retrobox.launcher import build_command, discover_games, find_core, load_config


class LauncherTests(unittest.TestCase):
    def test_discover_games_filters_extensions_case_insensitively_and_sorts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            for name in ("Zelda.NES", "mario.nes", "notes.txt", "subfolder"):
                path = folder / name
                if name == "subfolder":
                    path.mkdir()
                else:
                    path.touch()

            games = discover_games(
                {"folder": str(folder), "extensions": [".nes"]}
            )

            self.assertEqual([game.name for game in games], ["mario.nes", "Zelda.NES"])

    def test_discover_games_returns_empty_for_missing_folder(self):
        games = discover_games(
            {"folder": "/path/that/does/not/exist", "extensions": [".nes"]}
        )
        self.assertEqual(games, [])

    def test_find_core_checks_configured_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            core = Path(temporary_directory) / "nestopia_libretro.so"
            core.touch()

            self.assertEqual(
                find_core(core.name, [temporary_directory]),
                core,
            )

    def test_find_core_accepts_explicit_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            core = Path(temporary_directory) / "core.so"
            core.touch()
            self.assertEqual(find_core(str(core), []), core)

    def test_build_command_keeps_paths_as_individual_arguments(self):
        command = build_command(
            "/usr/bin/retroarch",
            Path("/cores/a core.so"),
            Path("/roms/a game.nes"),
        )
        self.assertEqual(
            command,
            ["/usr/bin/retroarch", "--verbose", "--libretro", "/cores/a core.so", "/roms/a game.nes"],
        )

    def test_load_config_requires_a_system_list(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "systems.json"
            config_path.write_text(json.dumps({"systems": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one system"):
                load_config(config_path)

    def test_load_config_resolves_relative_rom_folders_from_config_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            config_directory = project / "retrobox"
            config_directory.mkdir()
            config_path = config_directory / "systems.json"
            config_path.write_text(
                json.dumps({"systems": [{"folder": "../roms/nes"}]}),
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(
                Path(config["systems"][0]["folder"]),
                (project / "roms/nes").resolve(),
            )


if __name__ == "__main__":
    unittest.main()
