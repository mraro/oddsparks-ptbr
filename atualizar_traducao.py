# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "deep-translator>=1.11",
# ]
# ///
"""
OddSparks - Atualizador de Tradução PT-BR

Uso:
  uv run atualizar_traducao.py                           # auto-detecta instalação
  uv run atualizar_traducao.py "C:/Games/OddSparks"     # caminho explícito
  set ODDSPARKS_DIR=C:\\Games\\OddSparks && uv run atualizar_traducao.py

Após instalação via uv tool install:
  oddsparks-ptbr
  oddsparks-ptbr "C:/Games/OddSparks"
"""

import io
import json
import os
import shutil
import string
import subprocess
import sys
import urllib.request
import zipfile
import argparse

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WORK_DIR    = SCRIPT_DIR
REPAK       = os.path.join(WORK_DIR, "tools", "repak", "repak.exe")
CONFIG_FILE = os.path.join(WORK_DIR, "config.json")
EXTRACT_DIR = os.path.join(WORK_DIR, "extracted")
OUTPUT_DIR  = os.path.join(WORK_DIR, "output")

_STEAM_BASES = [
    "SteamLibrary\\steamapps\\common",
    "Steam\\steamapps\\common",
    "Program Files (x86)\\Steam\\steamapps\\common",
    "Program Files\\Steam\\steamapps\\common",
]
_GOG_BASES = [
    "GOG Games",
    "Games",
    "Program Files\\GOG Galaxy\\Games",
]

LOCRES_FILES = [
    ("OddsparksGame",      "OddsparksGame"),
    ("OddsparksDialogues", "OddsparksDialogues"),
    ("OddsparksQuests",    "OddsparksQuests"),
]

PATH_HASH_SEED  = 2535877449
REPAK_API_URL   = "https://api.github.com/repos/trumank/repak/releases/latest"


def step(msg):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}")


def run(cmd, **kwargs):
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"ERRO: {result.stderr}")
        sys.exit(1)
    return result.stdout


def _scan_drives_for_game():
    """Varre todas as letras de drive com padrões Steam e GOG."""
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.isdir(f"{d}:\\")]
    for drive in drives:
        for base in _STEAM_BASES:
            path = os.path.join(drive, base, "OddSparks")
            if os.path.isdir(path):
                return path
        for base in _GOG_BASES:
            path = os.path.join(drive, base, "OddSparks")
            if os.path.isdir(path):
                return path
    return None


def find_game_dir(cli_arg=None):
    if cli_arg:
        path = cli_arg.strip('"').strip("'")
        if os.path.isdir(path):
            return path
        print(f"ERRO: Diretório não encontrado: {path}")
        sys.exit(1)

    env = os.environ.get("ODDSPARKS_DIR", "")
    if env and os.path.isdir(env):
        print(f"  Usando ODDSPARKS_DIR: {env}")
        return env

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        saved = cfg.get("game_dir", "")
        if saved and os.path.isdir(saved):
            print(f"  Usando caminho salvo: {saved}")
            return saved

    # Repo clonado dentro da pasta do jogo → pai é o game dir
    parent = os.path.dirname(SCRIPT_DIR)
    if os.path.exists(os.path.join(parent, "Loc", "Content", "Paks", "Loc-Windows.pak")):
        print(f"  Jogo encontrado na pasta pai: {parent}")
        return parent

    # Varrer todas as letras de drive
    found = _scan_drives_for_game()
    if found:
        print(f"  Jogo encontrado em: {found}")
        return found

    print("Diretório do jogo não encontrado automaticamente.")
    print("Opções:")
    print('  1. Argumento: uv run atualizar_traducao.py "C:\\Games\\OddSparks"')
    print("  2. Variável:  set ODDSPARKS_DIR=C:\\Games\\OddSparks")
    game_dir = input("  3. Digite o caminho agora: ").strip().strip('"').strip("'")
    if not os.path.isdir(game_dir):
        print(f"ERRO: Diretório não encontrado: {game_dir}")
        sys.exit(1)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"game_dir": game_dir}, f, ensure_ascii=False, indent=2)
    print(f"  Caminho salvo em {CONFIG_FILE} para uso futuro.")
    return game_dir


def _get_repak_url():
    """Consulta a API do GitHub para obter a URL de download do release mais recente."""
    req = urllib.request.Request(
        REPAK_API_URL,
        headers={"User-Agent": "oddsparks-ptbr", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    for asset in data.get("assets", []):
        name = asset["name"]
        if "windows" in name.lower() and name.endswith(".zip"):
            return asset["browser_download_url"]
    raise RuntimeError(f"Asset Windows não encontrado. Assets disponíveis: {[a['name'] for a in data.get('assets', [])]}")


def ensure_repak():
    if os.path.exists(REPAK):
        return
    step("Baixando repak...")
    os.makedirs(os.path.dirname(REPAK), exist_ok=True)
    try:
        url = _get_repak_url()
        print(f"  {url}")
        data = urllib.request.urlopen(url).read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member in z.namelist():
                if member.lower().endswith("repak.exe"):
                    with z.open(member) as src, open(REPAK, "wb") as dst:
                        dst.write(src.read())
                    break
        print(f"  OK → {REPAK}")
    except Exception as e:
        print(f"ERRO ao baixar repak: {e}")
        print("Baixe manualmente em https://github.com/trumank/repak/releases")
        print(f"e coloque repak.exe em: {os.path.dirname(REPAK)}")
        sys.exit(1)


def extract_pak(pak_original):
    step("Extraindo pak do jogo...")
    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    run([REPAK, "unpack", pak_original, "--output", EXTRACT_DIR])
    print(f"  OK → {EXTRACT_DIR}")


def export_csvs():
    step("Exportando strings para CSV...")
    import locres_tool
    csvs = {}
    for folder, name in LOCRES_FILES:
        locres_path = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                                   folder, "en", f"{name}.locres")
        csv_path = os.path.join(WORK_DIR, f"{name}_en.csv")
        parsed = locres_tool.parse_locres(locres_path)
        locres_tool.export_csv(parsed, csv_path)
        print(f"  {name}: {len(parsed['strings'])} strings")
        csvs[name] = csv_path
    return csvs


def translate_csvs(csvs):
    step("Traduzindo strings novas (reutiliza cache)...")
    import translate as translate_mod
    cache_file = os.path.join(WORK_DIR, "translation_cache.json")
    translated = {}
    for name, csv_in in csvs.items():
        csv_out = os.path.join(WORK_DIR, f"{name}_ptbr.csv")
        translate_mod.translate_csv(csv_in, csv_out, batch_size=40, cache_file=cache_file)
        translated[name] = csv_out
    return translated


def build_locres(translated):
    step("Construindo arquivos .locres PT-BR...")
    import locres_tool
    for folder, name in LOCRES_FILES:
        locres_en = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                                 folder, "en", f"{name}.locres")
        locres_pt = os.path.join(EXTRACT_DIR, "Loc", "Content", "Localization",
                                 folder, "pt-BR", f"{name}.locres")
        os.makedirs(os.path.dirname(locres_pt), exist_ok=True)
        parsed       = locres_tool.parse_locres(locres_en)
        translations = locres_tool.apply_translations(parsed, translated[name])
        result       = locres_tool.build_locres(parsed, translations)
        with open(locres_pt, "wb") as f:
            f.write(result)
        print(f"  {name}: {os.path.getsize(locres_pt) // 1024} KB")


def repack():
    step("Reempacotando...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pak = os.path.join(OUTPUT_DIR, "Loc-Windows-ptBR.pak")
    run([REPAK, "pack",
         "--version", "V11",
         "--mount-point", "../../../",
         "--path-hash-seed", str(PATH_HASH_SEED),
         EXTRACT_DIR, out_pak])
    print(f"  Pak gerado: {os.path.getsize(out_pak) / (1024 * 1024):.1f} MB")
    return out_pak


def install(out_pak, pak_original):
    step("Instalando no jogo...")
    pak_backup = pak_original + ".backup"
    shutil.copy2(pak_original, pak_backup)
    print(f"  Backup: {pak_backup}")
    shutil.copy2(out_pak, pak_original)
    print(f"  Instalado: {pak_original}")
    return pak_backup


def main():
    parser = argparse.ArgumentParser(
        description="OddSparks - Atualizador de Tradução PT-BR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run atualizar_traducao.py\n"
            '  uv run atualizar_traducao.py "C:\\Games\\OddSparks"\n'
            "  oddsparks-ptbr                    (após: uv tool install .)"
        ),
    )
    parser.add_argument(
        "game_dir", nargs="?", default=None,
        metavar="PASTA_DO_JOGO",
        help="Caminho da instalação do OddSparks (auto-detectado se omitido)",
    )
    args = parser.parse_args()

    print("\n OddSparks Tradução PT-BR — Atualizador")
    print(" ========================================\n")

    game_dir     = find_game_dir(args.game_dir)
    pak_original = os.path.join(game_dir, "Loc", "Content", "Paks", "Loc-Windows.pak")

    if not os.path.exists(pak_original):
        print(f"ERRO: Pak não encontrado em {pak_original}")
        sys.exit(1)

    ensure_repak()
    extract_pak(pak_original)
    csvs        = export_csvs()
    translated  = translate_csvs(csvs)
    build_locres(translated)
    out_pak     = repack()
    pak_backup  = install(out_pak, pak_original)

    step("CONCLUÍDO!")
    print("  Reinicie o jogo para ver a tradução atualizada.")
    print(f"  Backup do pak anterior: {pak_backup}")


if __name__ == "__main__":
    main()
