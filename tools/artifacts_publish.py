#!/usr/bin/env python3
"""Publish editable FHD_Artifacts sources, and rebuild an install ZIP."""
from pathlib import Path
from zipfile import ZipFile
import argparse, hashlib, json, shutil, subprocess, sys, tempfile

NAME = "FHD_Artifacts_0.8.24.2_TEST_SMART_MAGNET_CARGO_LIMIT"
FOLDER = NAME + "_Nexus-GitHub"
GAMEZIP = NAME + ".zip"
ITEMS = "Mods/FHD_MODS/FHD_Artifacts/DATA/Items/"
GAI = "Mods/FHD_MODS/FHD_Artifacts/DATA/Effect/FHDTimeStone.gai"

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def kit(*args):
    subprocess.run([sys.executable, "-m", "srhd_modkit", *map(str, args)], check=True,
                   stdout=subprocess.DEVNULL)

def export():
    root = Path(__file__).resolve().parent.parent
    target = root / FOLDER
    if target.exists():
        raise RuntimeError("Existing source folder is protected: " + str(target))
    target.mkdir()
    zipfile = root / GAMEZIP
    shutil.copyfile(zipfile, target / "BASE_INSTALL.zip")
    gamehashes = []
    hashes = {}
    with ZipFile(zipfile) as z, tempfile.TemporaryDirectory() as tempdir:
        temp = Path(tempdir)
        items = []
        for record in z.infolist():
            if record.is_dir():
                continue
            data = z.read(record)
            gamehashes.append(digest(data) + "  " + record.filename)
            extension = Path(record.filename).suffix.lower()
            if extension in (".txt", ".ini"):
                dst = target / "SOURCE/EDITABLE_TEXT" / record.filename
            elif extension in (".dat", ".bmp"):
                dst = target / "SOURCE/EDITABLE_BINARY" / record.filename
            elif extension == ".gi" and record.filename.startswith(ITEMS):
                dst = temp / "items" / Path(record.filename).name
                items.append(dst)
            elif record.filename == GAI:
                dst = temp / "effect.gai"
            else:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            if dst.is_relative_to(target):
                hashes[dst.relative_to(target).as_posix()] = digest(data)
        output_icons = target / "SOURCE/ITEM_PNG"
        output_icons.mkdir(parents=True)
        kit("convert", "gi-png", *items, "--output", output_icons)
        extract = temp / "frames"
        extract.mkdir()
        kit("resource", "extract", temp / "effect.gai", extract)
        frames = [f for f in sorted(extract.glob("*.gi")) if f.stat().st_size]
        output_frames = target / "SOURCE/FRAME_PNG"
        output_frames.mkdir(parents=True)
        kit("convert", "gi-png", *frames, "--output", output_frames)
        for png in sorted((target / "SOURCE").rglob("*.png")):
            hashes[png.relative_to(target).as_posix()] = digest(png.read_bytes())
    assert len(gamehashes) == 58
    assert len(list(output_icons.glob("*.png"))) == 40
    assert len(list(output_frames.glob("*.png"))) == 39
    (target / "FILES_SHA256.txt").write_text("\n".join(gamehashes) + "\n", encoding="utf8")
    (target / "SOURCE_HASHES.json").write_text(
        json.dumps(hashes, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf8")
    checks = {"version": "0.8.24.2", "channel": "TEST", "mod_files": 58,
              "original_install_sha256": digest(zipfile.read_bytes()),
              "item_png": 40, "frame_png": 39, "in_game_tested": False,
              "dll_source_provided": False, "dat_editable_text_verified": False}
    (target / "CHECKS.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    shutil.copyfile(__file__, target / "BUILD.py")
    (target / "README_RU.md").write_text(
        "# FHD_Artifacts 0.8.24.2 — исходники для Nexus/GitHub\n\n"
        "Отдельная версия; другие версии не заменяются.\n\n"
        "BASE_INSTALL.zip — исходный установочный архив, 58 файлов, без изменений.\n"
        "SOURCE/EDITABLE_TEXT — оригинальные TXT/INI с сохранением кодировок.\n"
        "SOURCE/EDITABLE_BINARY — оригинальные DAT/BMP, без декомпиляции DAT.\n"
        "SOURCE/ITEM_PNG — 40 редактируемых PNG из GI.\n"
        "SOURCE/FRAME_PNG — 39 непустых кадров анимации GAI в PNG.\n"
        "SOURCE_HASHES.json, FILES_SHA256.txt — контрольные суммы.\n"
        "BUILD.py — сборка ZIP после точечных правок.\n\n"
        "Для проверки выполните: python BUILD.py --verify\n"
        "Для сборки изменённых PNG нужен Python-модуль srhd_modkit (XenoModKit).\n"
        "DLL представлены только в скомпилированном виде, исходники DLL не предоставлены.\n"
        "Обратная декомпиляция DAT в BlockPar TXT не проверена.\n"
        "В игре эта публикация не тестировалась. BUILD.py игру не запускает.\n",
        encoding="utf8")
    print("Source folder:", target, "files:", len(list(target.rglob("*"))))

def build(verify):
    project = Path(__file__).resolve().parent
    original = project / "BASE_INSTALL.zip"
    manifest = json.loads((project / "SOURCE_HASHES.json").read_text(encoding="utf8"))
    overlay = {}
    icons = []
    frames = []
    for rel, expected in manifest.items():
        path = project / rel
        raw = path.read_bytes()
        if digest(raw) == expected:
            continue
        if rel.startswith("SOURCE/EDITABLE_TEXT/"):
            overlay[rel.removeprefix("SOURCE/EDITABLE_TEXT/")] = raw
        elif rel.startswith("SOURCE/EDITABLE_BINARY/"):
            overlay[rel.removeprefix("SOURCE/EDITABLE_BINARY/")] = raw
        elif rel.startswith("SOURCE/ITEM_PNG/"):
            icons.append(path)
        elif rel.startswith("SOURCE/FRAME_PNG/"):
            frames.append(path)
        else:
            raise RuntimeError("Unrecognized edited file: " + rel)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for png in icons:
            out = tmp / ("icon_" + png.stem)
            out.mkdir()
            kit("convert", "png-gi", png, "--output", out)
            overlay[ITEMS + png.stem + ".gi"] = (out / (png.stem + ".gi")).read_bytes()
        if frames:
            gai = tmp / "old.gai"
            with ZipFile(original) as z:
                gai.write_bytes(z.read(GAI))
            extract = tmp / "frames"
            extract.mkdir()
            kit("resource", "extract", gai, extract)
            for png in frames:
                out = tmp / ("frame_" + png.stem)
                out.mkdir()
                kit("convert", "png-gi", png, "--output", out)
                shutil.copyfile(out / (png.stem + ".gi"), extract / (png.stem + ".gi"))
            new = tmp / "new.gai"
            kit("resource", "build-gai", extract, "--template", gai, "--output", new)
            overlay[GAI] = new.read_bytes()
    dest = project / "DIST" / (NAME + "_INSTALL.zip")
    dest.parent.mkdir(exist_ok=True)
    if not overlay:
        shutil.copyfile(original, dest)
    else:
        with ZipFile(original) as zin, ZipFile(dest, "w") as zout:
            assert set(overlay) <= set(zin.namelist())
            for info in zin.infolist():
                zout.writestr(info, overlay.get(info.filename, zin.read(info.filename)))
    with ZipFile(original) as zin, ZipFile(dest) as zout:
        assert zin.namelist() == zout.namelist()
        for name in zin.namelist():
            if name not in overlay and zin.read(name) != zout.read(name):
                raise RuntimeError("Unmodified file was altered: " + name)
        if verify:
            for line in (project / "FILES_SHA256.txt").read_text(encoding="utf8").splitlines():
                expected, name = line.split("  ", 1)
                if name not in overlay and digest(zout.read(name)) != expected:
                    raise RuntimeError("Invalid SHA256: " + name)
    print("Built:", dest, "modified:", len(overlay), "SHA256:", digest(dest.read_bytes()))

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--export", action="store_true")
    args.add_argument("--verify", action="store_true")
    opts = args.parse_args()
    if opts.export:
        export()
    else:
        build(opts.verify)
