# OddSparks PT-BR Translation Tools

Ferramentas para traduzir o jogo **OddSparks** (Unreal Engine 5) para Português do Brasil.

Traduz automaticamente os arquivos `.locres` do jogo usando Google Translate, preservando todo o markup UE5 (`<b>`, `<img/>`, `{variáveis}`, etc.).

## O que é traduzido

| Arquivo | Conteúdo | Strings |
|---|---|---|
| `OddsparksGame` | Interface, menus, tooltips | ~3.387 |
| `OddsparksDialogues` | Diálogos dos personagens | ~808 |
| `OddsparksQuests` | Missões e objetivos | ~473 |

## Requisitos

- Python 3.10+
- [repak](https://github.com/trumank/repak/releases) (baixado automaticamente)
- Jogo instalado via GOG/Steam em `D:\01_JOGOS_INSTALADOS\OddSparks`

```bash
pip install deep-translator
```

## Instalação rápida (primeira vez)

```bash
git clone https://github.com/SEU_USUARIO/oddsparks-ptbr
cd oddsparks-ptbr

# Ajuste os caminhos no topo de atualizar_traducao.py se necessário
python atualizar_traducao.py
```

O script faz tudo automaticamente:
1. Baixa o repak
2. Extrai o pak do jogo
3. Traduz as strings (Google Translate + cache)
4. Reconstrói e instala

## Atualizar após patch do jogo

```bash
python atualizar_traducao.py
```

Só traduz strings **novas** — reutiliza o cache das já traduzidas. Rápido.

## Uso manual (avançado)

### Exportar strings para CSV
```bash
python locres_tool.py export "caminho/en/OddsparksGame.locres" saida.csv
```

### Construir .locres com traduções
```bash
python locres_tool.py build "caminho/en/OddsparksGame.locres" saida.csv "caminho/pt-BR/OddsparksGame.locres"
```

### Ver informações de um .locres
```bash
python locres_tool.py info "caminho/OddsparksGame.locres"
```

### Traduzir um CSV
```bash
python translate.py entrada_en.csv saida_ptbr.csv --batch 40
```

## Forçar o idioma PT-BR

Se o jogo não carregar PT-BR automaticamente, use o launcher:

**Windows:** Execute `Iniciar_em_Portugues.bat` na pasta do jogo.

Ou inicie com a flag: `Oddsparks.exe -culture=pt-BR`

## Como funciona

```
Loc-Windows.pak
    └── Loc/Content/Localization/
            ├── OddsparksGame/en/OddsparksGame.locres   ← extrai
            ├── OddsparksDialogues/en/...locres          ← extrai
            └── OddsparksQuests/en/...locres             ← extrai
                        ↓
               parse binário .locres (v3)
                        ↓
               exporta → CSV (index, en, pt-BR)
                        ↓
               Google Translate (com cache)
                        ↓
               reconstrói .locres (UTF-16 para acentos)
                        ↓
            ├── OddsparksGame/pt-BR/...locres   ← adiciona
            ├── OddsparksDialogues/pt-BR/...    ← adiciona
            └── OddsparksQuests/pt-BR/...       ← adiciona
                        ↓
               repak → novo Loc-Windows.pak
                        ↓
               instala no jogo
```

## Formato .locres (UE5 v3)

```
[16 bytes] Magic
[1 byte]   Version = 3
[8 bytes]  StringDataOffset (int64)
[4 bytes]  EntriesCount (int32)
[N bytes]  Entries (key hashes → string indices)
--- StringDataOffset ---
[4 bytes]  StringCount (int32)
[...]      Strings: FString (length + chars) + RefCount (int32)
           length > 0 → ANSI/ASCII
           length < 0 → UTF-16 LE (necessário para acentos)
```

## Reverter para inglês

```bash
# O backup é criado automaticamente antes de cada instalação
copy "D:\01_JOGOS_INSTALADOS\OddSparks\Loc\Content\Paks\Loc-Windows.pak.backup" ^
     "D:\01_JOGOS_INSTALADOS\OddSparks\Loc\Content\Paks\Loc-Windows.pak"
```

## Estrutura do projeto

```
oddsparks-ptbr/
├── locres_tool.py          # Parser/builder de .locres
├── translate.py            # Tradução automática com Google Translate
├── atualizar_traducao.py   # Script de atualização completo
└── README.md
```

## Contribuindo

Correções de tradução são bem-vindas. Edite os arquivos `*_ptbr.csv` e abra um Pull Request.

O cache em `translation_cache.json` é local e não está no repositório (contém strings do jogo).

## Licença

MIT — ferramentas livres para uso pessoal. O conteúdo traduzido pertence aos criadores do OddSparks ([Massive Miniteam](https://www.massiveminiteam.com/)).
