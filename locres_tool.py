"""
OddSparks .locres parser/writer para tradução PT-BR
Formato: UE5 LocRes v3 (Compact/OptimizedCompact)
"""

import struct
import json
import os
import sys

LOCRES_MAGIC = bytes([0x0E, 0x14, 0x74, 0x75, 0x67, 0x4A, 0x03, 0xFC,
                      0x4A, 0x15, 0x90, 0x9D, 0xC3, 0x37, 0x7F, 0x1B])


def read_fstring(data: bytes, pos: int) -> tuple[str | None, int]:
    """Lê uma FString do formato binário UE. Retorna (string, nova_posição)."""
    length = struct.unpack_from('<i', data, pos)[0]
    pos += 4
    if length == 0:
        return None, pos
    if length < 0:
        # UTF-16 (TCHAR)
        char_count = -length
        raw = data[pos:pos + char_count * 2]
        pos += char_count * 2
        text = raw.decode('utf-16-le').rstrip('\x00')
    else:
        # ANSI
        raw = data[pos:pos + length]
        pos += length
        text = raw.decode('latin-1').rstrip('\x00')
    return text, pos


def write_fstring(text: str | None) -> bytes:
    """Serializa uma FString para binário UE."""
    if text is None:
        return struct.pack('<i', 0)
    # UE5: strings com caracteres não-ASCII devem usar UTF-16 (length negativo)
    # Strings puramente ASCII podem usar ANSI (length positivo)
    if any(ord(c) > 127 for c in text):
        encoded = (text + '\x00').encode('utf-16-le')
        char_count = len(encoded) // 2
        return struct.pack('<i', -char_count) + encoded
    else:
        encoded = (text + '\x00').encode('ascii')
        return struct.pack('<i', len(encoded)) + encoded


def parse_locres(path: str) -> dict:
    """Parseia um arquivo .locres e retorna estrutura com strings e entradas."""
    with open(path, 'rb') as f:
        data = f.read()

    pos = 0

    # Verificar magic
    magic = data[pos:pos + 16]
    pos += 16
    assert magic == LOCRES_MAGIC, f"Magic inválido: {magic.hex()}"

    version = data[pos]
    pos += 1
    assert version == 3, f"Versão não suportada: {version}"

    string_data_offset = struct.unpack_from('<q', data, pos)[0]
    pos += 8

    entries_count = struct.unpack_from('<i', data, pos)[0]
    pos += 4

    # Ler entradas (chave -> índice de string)
    # Descobrir tamanho: o bloco de entradas vai de pos até string_data_offset
    entries_block_size = string_data_offset - pos
    entries_data = data[pos:string_data_offset]
    pos = string_data_offset

    # Ler tabela de strings
    string_count = struct.unpack_from('<i', data, pos)[0]
    pos += 4

    strings = []
    for _ in range(string_count):
        s, pos = read_fstring(data, pos)
        ref_count = struct.unpack_from('<i', data, pos)[0]
        pos += 4
        strings.append({'text': s, 'ref_count': ref_count})

    return {
        'version': version,
        'entries_block': entries_data,
        'entries_count': entries_count,
        'strings': strings,
    }


def export_csv(parsed: dict, output_path: str):
    """Exporta strings para CSV."""
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(['index', 'ref_count', 'en', 'pt-BR'])
        for i, s in enumerate(parsed['strings']):
            text = s['text'] if s['text'] is not None else ''
            writer.writerow([i, s['ref_count'], text, ''])


def build_locres(parsed: dict, translated_strings: list[str | None]) -> bytes:
    """Reconstrói um .locres com as strings traduzidas."""
    # String table
    string_table = bytearray()
    string_table += struct.pack('<i', len(translated_strings))
    for i, orig in enumerate(parsed['strings']):
        text = translated_strings[i] if i < len(translated_strings) else orig['text']
        string_table += write_fstring(text)
        string_table += struct.pack('<i', orig['ref_count'])

    # Calcular offsets
    # Header: magic(16) + version(1) + string_data_offset(8) + entries_count(4) = 29 bytes
    header_size = 29
    entries_block = parsed['entries_block']
    string_data_offset = header_size + len(entries_block)

    # Montar arquivo
    out = bytearray()
    out += LOCRES_MAGIC
    out += struct.pack('<B', 3)
    out += struct.pack('<q', string_data_offset)
    out += struct.pack('<i', parsed['entries_count'])
    out += entries_block
    out += string_table

    return bytes(out)


def apply_translations(parsed: dict, csv_path: str) -> list[str | None]:
    """Lê o CSV traduzido e retorna lista de strings PT-BR."""
    import csv
    translations = {i: s['text'] for i, s in enumerate(parsed['strings'])}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row['index'])
            pt = row['pt-BR'].strip()
            if pt:
                translations[idx] = pt

    return [translations.get(i, parsed['strings'][i]['text'])
            for i in range(len(parsed['strings']))]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Ferramenta de tradução .locres OddSparks')
    sub = parser.add_subparsers(dest='cmd')

    p_export = sub.add_parser('export', help='Exportar strings para CSV')
    p_export.add_argument('locres', help='Arquivo .locres de entrada')
    p_export.add_argument('csv', help='Arquivo CSV de saída')

    p_build = sub.add_parser('build', help='Construir .locres traduzido')
    p_build.add_argument('locres', help='Arquivo .locres original (en)')
    p_build.add_argument('csv', help='CSV com traduções preenchidas')
    p_build.add_argument('output', help='Arquivo .locres de saída')

    p_info = sub.add_parser('info', help='Mostrar informações do .locres')
    p_info.add_argument('locres', help='Arquivo .locres')

    args = parser.parse_args()

    if args.cmd == 'export':
        parsed = parse_locres(args.locres)
        export_csv(parsed, args.csv)
        print(f"Exportado {len(parsed['strings'])} strings para {args.csv}")

    elif args.cmd == 'build':
        parsed = parse_locres(args.locres)
        translated = apply_translations(parsed, args.csv)
        result = build_locres(parsed, translated)
        with open(args.output, 'wb') as f:
            f.write(result)
        count = sum(1 for i, s in enumerate(translated)
                    if i < len(parsed['strings']) and s != parsed['strings'][i]['text'])
        print(f"Construído {args.output} com {count} strings traduzidas")

    elif args.cmd == 'info':
        parsed = parse_locres(args.locres)
        print(f"Versão: {parsed['version']}")
        print(f"Entradas: {parsed['entries_count']}")
        print(f"Strings únicas: {len(parsed['strings'])}")
        print("\nPrimeiras 20 strings:")
        for i, s in enumerate(parsed['strings'][:20]):
            print(f"  [{i}] {repr(s['text'])}")
    else:
        parser.print_help()
