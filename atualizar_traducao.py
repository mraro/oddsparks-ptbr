"""
OddSparks - Atualizador de Tradução PT-BR
Uso: python atualizar_traducao.py

Detecta strings novas após update do jogo, traduz só as novas
(reutiliza cache das já traduzidas) e reinstala automaticamente.
"""

import os
import sys
import csv
import time
import shutil
import struct
import subprocess
import json

GAME_DIR     = r"D:\01_JOGOS_INSTALADOS\OddSparks"
WORK_DIR     = r"D:\OddSparks_Translation"
REPAK        = r"D:\OddSparks_Translation\tools\repak\repak.exe"
PAK_ORIGINAL = os.path.join(GAME_DIR, r"Loc\Content\Paks\Loc-Windows.pak")
PAK_BACKUP   = PAK_ORIGINAL + ".backup"
EXTRACT_DIR  = os.path.join(WORK_DIR, "extracted")
OUTPUT_DIR   = os.path.join(WORK_DIR, "output")
CACHE_FILE   = os.path.join(WORK_DIR, "translation_cache.json")

LOCRES_FILES = [
    ("OddsparksGame",      "OddsparksGame"),
    ("OddsparksDialogues", "OddsparksDialogues"),
    ("OddsparksQuests",    "OddsparksQuests"),
]

PATH_HASH_SEED = 2535877449


def run(cmd, **kwargs):
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"ERRO: {result.stderr}")
        sys.exit(1)
    return result.stdout


def step(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print('='*50)


def extract_pak():
    step("Extraindo pak do jogo...")
    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    run([REPAK, "unpack", PAK_ORIGINAL, "--output", EXTRACT_DIR])
    print(f"  OK - extraído para {EXTRACT_DIR}")


def export_csvs():
    step("Exportando strings para CSV...")
    csvs = {}
    for folder, name in LOCRES_FILES:
        locres = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                              folder, "en", f"{name}.locres")
        csv_path = os.path.join(WORK_DIR, f"{name}_en.csv")
        run([sys.executable, os.path.join(WORK_DIR, "locres_tool.py"),
             "export", locres, csv_path])
        with open(csv_path, encoding='utf-8') as f:
            count = sum(1 for _ in csv.DictReader(f))
        print(f"  {name}: {count} strings")
        csvs[name] = csv_path
    return csvs


def translate_csvs(csvs):
    step("Traduzindo strings novas (reutiliza cache)...")
    translated = {}
    for name, csv_in in csvs.items():
        csv_out = os.path.join(WORK_DIR, f"{name}_ptbr.csv")
        run([sys.executable, os.path.join(WORK_DIR, "translate.py"),
             csv_in, csv_out, "--batch", "40"])
        translated[name] = csv_out
    return translated


def build_locres(translated):
    step("Construindo arquivos .locres PT-BR...")
    for folder, name in LOCRES_FILES:
        locres_en = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                                 folder, "en", f"{name}.locres")
        locres_pt = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                                 folder, "pt-BR", f"{name}.locres")
        os.makedirs(os.path.dirname(locres_pt), exist_ok=True)
        csv_pt = translated[name]
        run([sys.executable, os.path.join(WORK_DIR, "locres_tool.py"),
             "build", locres_en, csv_pt, locres_pt])
        size = os.path.getsize(locres_pt)
        print(f"  {name}: {size//1024} KB")


def repack():
    step("Reempacotando...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pak = os.path.join(OUTPUT_DIR, "Loc-Windows-ptBR.pak")
    run([REPAK, "pack",
         "--version", "V11",
         "--mount-point", "../../../",
         "--path-hash-seed", str(PATH_HASH_SEED),
         EXTRACT_DIR, out_pak])
    size = os.path.getsize(out_pak) / (1024*1024)
    print(f"  Pak gerado: {size:.1f} MB")
    return out_pak


def install(out_pak):
    step("Instalando no jogo...")
    shutil.copy2(PAK_ORIGINAL, PAK_BACKUP)
    print(f"  Backup: {PAK_BACKUP}")
    shutil.copy2(out_pak, PAK_ORIGINAL)
    print(f"  Instalado: {PAK_ORIGINAL}")


def main():
    print("\n OddSparks Tradução PT-BR - Atualizador")
    print(" ========================================\n")

    if not os.path.exists(PAK_ORIGINAL):
        print(f"ERRO: Pak não encontrado em {PAK_ORIGINAL}")
        sys.exit(1)

    extract_pak()
    csvs = export_csvs()
    translated = translate_csvs(csvs)
    build_locres(translated)
    out_pak = repack()
    install(out_pak)

    step("CONCLUÍDO!")
    print("  Reinicie o jogo para ver a tradução atualizada.")
    print(f"  Backup do pak anterior: {PAK_BACKUP}")


if __name__ == "__main__":
    main()
