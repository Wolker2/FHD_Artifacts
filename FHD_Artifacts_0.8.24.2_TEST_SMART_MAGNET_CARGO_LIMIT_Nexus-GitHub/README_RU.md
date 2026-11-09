# FHD_Artifacts 0.8.24.2 — исходники для Nexus/GitHub

Отдельная версия; другие версии не заменяются.

BASE_INSTALL.zip — исходный установочный архив, 58 файлов, без изменений.
SOURCE/EDITABLE_TEXT — оригинальные TXT/INI с сохранением кодировок.
SOURCE/EDITABLE_BINARY — оригинальные DAT/BMP, без декомпиляции DAT.
SOURCE/ITEM_PNG — 40 редактируемых PNG из GI.
SOURCE/FRAME_PNG — 39 непустых кадров анимации GAI в PNG.
SOURCE_HASHES.json, FILES_SHA256.txt — контрольные суммы.
BUILD.py — сборка ZIP после точечных правок.

Для проверки выполните: python BUILD.py --verify
Для сборки изменённых PNG нужен Python-модуль srhd_modkit (XenoModKit).
DLL представлены только в скомпилированном виде, исходники DLL не предоставлены.
Обратная декомпиляция DAT в BlockPar TXT не проверена.
В игре эта публикация не тестировалась. BUILD.py игру не запускает.
