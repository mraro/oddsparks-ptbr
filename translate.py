# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "deep-translator>=1.11",
# ]
# ///
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

_DEFAULT_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_cache.json")

MARKUP_PATTERNS = [
    r'<img[^>]*/?>',
    r'<[a-zA-Z][^>]*/?>',
    r'</>',
    r'</[a-zA-Z]+>',
    r'<[a-zA-Z][^>]*>',
    r'\{[^}]+\}',
    r'SimActor="[^"]*"',
]

PLACEHOLDER_RE = re.compile('|'.join(MARKUP_PATTERNS))


def protect_markup(text: str) -> tuple[str, list[str]]:
    markups = []
    counter = [0]

    def replacer(m):
        idx = counter[0]
        counter[0] += 1
        markups.append(m.group(0))
        return f'§{idx}§'

    return PLACEHOLDER_RE.sub(replacer, text), markups


def restore_markup(text: str, markups: list[str]) -> str:
    for i, m in enumerate(markups):
        text = text.replace(f'§{i}§', m)
    return text


def needs_translation(text: str | None) -> bool:
    if not text:
        return False
    clean = PLACEHOLDER_RE.sub('', text).strip()
    if not clean:
        return False
    if re.match(r'^[\d\s\.\,\+\-\*\/\%\(\)\[\]\{\}\!\?\:\;\=\<\>]+$', clean):
        return False
    return bool(re.search(r'[a-zA-Z]', clean))


def load_cache(cache_file: str = _DEFAULT_CACHE) -> dict:
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache: dict, cache_file: str = _DEFAULT_CACHE):
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def translate_batch(texts: list[str], translator: GoogleTranslator) -> list[str]:
    protected, all_markups = [], []
    for text in texts:
        clean, markups = protect_markup(text)
        protected.append(clean)
        all_markups.append(markups)

    try:
        results = translator.translate_batch(protected)
    except Exception as e:
        print(f"  Erro no lote: {e}, tentando um por um...")
        results = []
        for text in protected:
            try:
                results.append(translator.translate(text))
                time.sleep(0.5)
            except Exception as e2:
                print(f"  Erro individual: {e2}")
                results.append(text)

    return [
        restore_markup(r if r is not None else '', m)
        for r, m in zip(results, all_markups)
    ]


def translate_csv(
    input_csv: str,
    output_csv: str,
    batch_size: int = 50,
    cache_file: str = _DEFAULT_CACHE,
):
    cache      = load_cache(cache_file)
    translator = GoogleTranslator(source='en', target='pt')

    with open(input_csv, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f"Total de strings: {total}")

    to_translate = [
        (i, row) for i, row in enumerate(rows)
        if needs_translation(row['en']) and not row['pt-BR'].strip()
    ]
    print(f"Strings para traduzir: {len(to_translate)}")

    cached, still_needed = 0, []
    for i, row in to_translate:
        if row['en'] in cache:
            rows[i]['pt-BR'] = cache[row['en']]
            cached += 1
        else:
            still_needed.append((i, row))

    print(f"Do cache: {cached} | Novas: {len(still_needed)}")

    total_batches = (len(still_needed) + batch_size - 1) // batch_size
    for batch_num, start in enumerate(range(0, len(still_needed), batch_size), 1):
        batch      = still_needed[start:start + batch_size]
        batch_texts = [row['en'] for _, row in batch]
        print(f"Lote {batch_num}/{total_batches} ({len(batch)} strings)...", end=' ', flush=True)
        translated = translate_batch(batch_texts, translator)
        for (i, row), pt in zip(batch, translated):
            rows[i]['pt-BR'] = pt
            cache[row['en']] = pt
        save_cache(cache, cache_file)
        print("OK")
        time.sleep(1.5)

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'ref_count', 'en', 'pt-BR'],
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    count = sum(1 for r in rows if r['pt-BR'].strip())
    print(f"\nSalvo em {output_csv}: {count}/{total} strings traduzidas")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Traduz CSV de strings EN → PT-BR")
    parser.add_argument('input_csv')
    parser.add_argument('output_csv')
    parser.add_argument('--batch', type=int, default=50)
    parser.add_argument('--cache', default=_DEFAULT_CACHE, help='Arquivo de cache JSON')
    args = parser.parse_args()

    translate_csv(args.input_csv, args.output_csv, args.batch, cache_file=args.cache)
