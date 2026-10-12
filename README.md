# RetroBox

RetroBox is a small, keyboard-friendly multi-system game launcher for Raspberry Pi 4B. It finds games in per-system folders and starts them with RetroArch and the selected libretro core. RetroBox is a frontend; it does not implement console hardware itself.

## Raspberry Pi setup

1. Install Raspberry Pi OS with a desktop environment and RetroArch. Install the libretro cores you want using RetroArch's Online Updater or your distribution's package manager. The default systems use Nestopia (NES), Snes9x (SNES), Gambatte (GB/GBC), mGBA (GBA), Genesis Plus GX (Genesis), and PCSX ReARMed (PlayStation).
2. If Tkinter is missing, install the `python3-tk` package using your OS package manager.
3. Put game files in the project `roms/` folders (for example, `roms/nes/`). The workspace includes Tiny Golf and Quarti for NES, Dangan GB2 for Game Boy Color, and GBA Microjam '23 for GBA. Create other per-system folders as needed.
4. Check `retrobox/systems.json`. Set `retroarch` to the RetroArch executable if it is not on `PATH`, and make sure `core_directories` includes the directory containing your installed `*_libretro.so` files. Edit system folders, core filenames, or supported extensions there as needed.
5. From this project directory, run `python3 -m retrobox`.

### Start RetroBox automatically

On the Raspberry Pi desktop, run `sh scripts/configure_autostart.sh` from this project directory. This creates a per-user desktop autostart entry, so RetroBox opens when that user logs into the graphical desktop. To remove it, run `sh scripts/configure_autostart.sh remove`. This is desktop-login startup, not a headless boot service; the GUI needs a graphical session. Startup output is logged to `~/.local/state/retrobox/launcher.log`.

Use the arrow keys to select a game and press Enter, or double-click it. A wired Xbox controller can use its D-pad or left stick to browse games, left/right to change systems, and **A** to launch. This reads Linux's `/dev/input/js*` joystick interface and adds no Python dependency. RetroArch handles in-game controller input; its controller autoconfiguration or input bindings must be set up separately.

If the controller is not detected, connect it before starting RetroBox and check that Linux exposes a device such as `/dev/input/js0`. Controller support in games also requires RetroArch and an installed core, which are not included in the low-data GUI setup.

To use a separate configuration file, run `python3 -m retrobox --config /path/to/systems.json`.

## Notes

- The included games are homebrew releases. Additional ROMs, BIOS files, RetroArch, and libretro cores are not bundled. Only use game files and firmware you are legally entitled to use.
- Core availability and performance vary by Raspberry Pi OS version and architecture. Some systems, especially PlayStation, may require BIOS files configured separately in RetroArch.
- RetroBox launches a core directly with RetroArch; it does not manage downloads, scraping, save states, or controller configuration.

## Run tests

Run `python3 -m unittest discover -s tests -v` from the project directory. Tests use only Python's standard library and do not need a display, RetroArch, cores, or ROMs.
