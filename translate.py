"""
Tradução automática de strings do OddSparks EN → PT-BR
Protege markup UE (<b>, <img/>, {vars}, etc.) durante tradução.
"""

import re
import json
import time
import csv
import os
import sys
from deep_translator import GoogleTranslator

CACHE_FILE = "D:\\OddSparks_Translation\\translation_cache.json"

# Padrões de markup que devem ser preservados
MARKUP_PATTERNS = [
    r'<img[^>]*/?>',           # <img id="..." />
    r'<[a-zA-Z][^>]*/?>',     # tags autofeachadas
    r'</>',                     # tag de fechamento genérica
    r'</[a-zA-Z]+>',           # tags de fechamento
    r'<[a-zA-Z][^>]*>',       # tags de abertura
    r'\{[^}]+\}',             # {variáveis}
    r'SimActor="[^"]*"',      # atributos SimActor
]

PLACEHOLDER_RE = re.compile('|'.join(MARKUP_PATTERNS))


def protect_markup(text: str) -> tuple[str, list[str]]:
    """Substitui markup por placeholders §N§ e retorna (texto_limpo, lista_de_markups)."""
    markups = []
    counter = [0]

    def replacer(m):
        idx = counter[0]
        counter[0] += 1
        markups.append(m.group(0))
        return f'§{idx}§'

    clean = PLACEHOLDER_RE.sub(replacer, text)
    return clean, markups


def restore_markup(text: str, markups: list[str]) -> str:
    """Restaura placeholders §N§ de volta para o markup original."""
    for i, m in enumerate(markups):
        text = text.replace(f'§{i}§', m)
    return text


def needs_translation(text: str | None) -> bool:
    """Verifica se o texto precisa de tradução (tem conteúdo textual real)."""
    if not text:
        return False
    # Remove markup e whitespace
    clean = PLACEHOLDER_RE.sub('', text).strip()
    if not clean:
        return False
    # Só números, símbolos matemáticos, ou strings muito curtas sem letras
    if re.match(r'^[\d\s\.\,\+\-\*\/\%\(\)\[\]\{\}\!\?\:\;\=\<\>]+$', clean):
        return False
    # Tem pelo menos uma letra
    return bool(re.search(r'[a-zA-Z]', clean))


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_batch(texts: list[str], translator: GoogleTranslator) -> list[str]:
    """Traduz um lote de textos protegendo o markup."""
    protected = []
    all_markups = []

    for text in texts:
        clean, markups = protect_markup(text)
        protected.append(clean)
        all_markups.append(markups)

    # Traduzir em lote
    try:
        results = translator.translate_batch(protected)
    except Exception as e:
        print(f"  Erro no lote: {e}, tentando um por um...")
        results = []
        for text in protected:
            try:
                r = translator.translate(text)
                results.append(r)
                time.sleep(0.5)
            except Exception as e2:
                print(f"  Erro individual: {e2}")
                results.append(text)

    # Restaurar markup
    final = []
    for translated, markups in zip(results, all_markups):
        if translated is None:
            translated = ''
        restored = restore_markup(translated, markups)
        final.append(restored)

    return final


def translate_csv(input_csv: str, output_csv: str, batch_size: int = 50):
    """Traduz strings de um CSV exportado pelo locres_tool.py."""
    cache = load_cache()
    translator = GoogleTranslator(source='en', target='pt')

    # Ler CSV
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    print(f"Total de strings: {total}")

    # Filtrar quais precisam de tradução
    to_translate = [(i, row) for i, row in enumerate(rows)
                    if needs_translation(row['en']) and not row['pt-BR'].strip()]

    print(f"Strings para traduzir: {len(to_translate)}")

    # Preencher do cache primeiro
    cached = 0
    still_needed = []
    for i, row in to_translate:
        en = row['en']
        if en in cache:
            rows[i]['pt-BR'] = cache[en]
            cached += 1
        else:
            still_needed.append((i, row))

    print(f"Do cache: {cached} | Novas: {len(still_needed)}")

    # Traduzir em lotes
    for start in range(0, len(still_needed), batch_size):
        batch = still_needed[start:start + batch_size]
        batch_idx = [i for i, _ in batch]
        batch_texts = [row['en'] for _, row in batch]

        batch_num = start // batch_size + 1
        total_batches = (len(still_needed) + batch_size - 1) // batch_size
        print(f"Lote {batch_num}/{total_batches} ({len(batch)} strings)...", end=' ', flush=True)

        translated = translate_batch(batch_texts, translator)

        for (i, row), pt in zip(batch, translated):
            rows[i]['pt-BR'] = pt
            cache[row['en']] = pt

        save_cache(cache)
        print("OK")
        time.sleep(1.5)

    # Salvar CSV com traduções
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'ref_count', 'en', 'pt-BR'],
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    count = sum(1 for r in rows if r['pt-BR'].strip())
    print(f"\nSalvo em {output_csv}: {count}/{total} strings traduzidas")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    parser.add_argument('--batch', type=int, default=50)
    args = parser.parse_args()

    translate_csv(args.input_csv, args.output_csv, args.batch)
