# RetroBox

RetroBox is a small, keyboard-friendly multi-system game launcher for Raspberry Pi 4B. It finds games in per-system folders and starts them with RetroArch and the selected libretro core. RetroBox is a frontend; it does not implement console hardware itself.

## Raspberry Pi setup

1. Install Raspberry Pi OS with a desktop environment and RetroArch. Install the libretro cores you want using RetroArch's Online Updater or your distribution's package manager. The default systems use Nestopia (NES), Snes9x (SNES), Gambatte (GB/GBC), mGBA (GBA), Genesis Plus GX (Genesis), and PCSX ReARMed (PlayStation).
2. If Tkinter is missing, install the `python3-tk` package using your OS package manager.
3. Copy your own legally obtained game files into the folders under `~/RetroBox/roms/` (for example, `~/RetroBox/roms/nes/`). The launcher creates no ROM folders automatically; create whichever ones you use.
4. Check `retrobox/systems.json`. Set `retroarch` to the RetroArch executable if it is not on `PATH`, and make sure `core_directories` includes the directory containing your installed `*_libretro.so` files. Edit system folders, core filenames, or supported extensions there as needed.
5. From this project directory, run `python3 -m retrobox`.

Use the arrow keys to select a game and press Enter, or double-click it. The Play Game button also launches the selected entry. RetroArch handles gamepad mappings and saves according to its own configuration.

To use a separate configuration file, run `python3 -m retrobox --config /path/to/systems.json`.

## Notes

- ROMs, BIOS files, RetroArch, and libretro cores are not bundled. Only use game files and firmware you are legally entitled to use.
- Core availability and performance vary by Raspberry Pi OS version and architecture. Some systems, especially PlayStation, may require BIOS files configured separately in RetroArch.
- RetroBox launches a core directly with RetroArch; it does not manage downloads, scraping, save states, or controller configuration.

## Run tests

Run `python3 -m unittest discover -s tests -v` from the project directory. Tests use only Python's standard library and do not need a display, RetroArch, cores, or ROMs.
