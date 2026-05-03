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

- Python 3.10+ **ou** [uv](https://docs.astral.sh/uv/getting-started/installation/) (recomendado — instala dependências automaticamente)
- [repak](https://github.com/trumank/repak/releases) — baixado automaticamente na primeira execução
- OddSparks instalado (Steam, GOG ou outro)

## Instalação rápida

```bash
git clone https://github.com/mraro/oddsparks-ptbr
cd oddsparks-ptbr
uv run atualizar_traducao.py
```

O script detecta a instalação do jogo automaticamente nos caminhos padrão do Steam e GOG.
Se não encontrar, pede o caminho interativamente e salva para uso futuro.

### Passando o caminho do jogo diretamente

```bash
uv run atualizar_traducao.py "C:\Games\OddSparks"
```

### Via variável de ambiente

```bash
set ODDSPARKS_DIR=C:\Games\OddSparks
uv run atualizar_traducao.py
```

### Sem uv (com pip)

```bash
pip install deep-translator
python atualizar_traducao.py
python atualizar_traducao.py "C:\Games\OddSparks"
```

### Instalação global como ferramenta (uv tool)

```bash
uv tool install .
oddsparks-ptbr
oddsparks-ptbr "C:\Games\OddSparks"
```

O script faz tudo automaticamente:
1. Baixa o repak (se necessário)
2. Extrai o pak do jogo
3. Traduz as strings (Google Translate + cache local)
4. Reconstrói e instala

## Atualizar após patch do jogo

```bash
uv run atualizar_traducao.py
```

Só traduz strings **novas** — reutiliza o cache das já traduzidas. Rápido.

## Uso manual (avançado)

### Exportar strings para CSV
```bash
uv run locres_tool.py export "caminho/en/OddsparksGame.locres" saida.csv
```

### Construir .locres com traduções
```bash
uv run locres_tool.py build "caminho/en/OddsparksGame.locres" saida.csv "caminho/pt-BR/OddsparksGame.locres"
```

### Ver informações de um .locres
```bash
uv run locres_tool.py info "caminho/OddsparksGame.locres"
```

### Traduzir um CSV
```bash
uv run translate.py entrada_en.csv saida_ptbr.csv --batch 40
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

Um backup é criado automaticamente antes de cada instalação com o sufixo `.backup`.
Para reverter, copie o backup de volta:

```
Loc-Windows.pak.backup  →  Loc-Windows.pak
```

Caminho padrão Steam: `<SteamLibrary>\steamapps\common\OddSparks\Loc\Content\Paks\`

## Estrutura do projeto

```
oddsparks-ptbr/
├── locres_tool.py          # Parser/builder de .locres
├── translate.py            # Tradução automática com Google Translate
├── atualizar_traducao.py   # Script de atualização completo
├── pyproject.toml          # Definição do pacote uv/pip
└── README.md
```

## Contribuindo

Correções de tradução são bem-vindas. Edite os arquivos `*_ptbr.csv` e abra um Pull Request.

O cache em `translation_cache.json` é local e não está no repositório (contém strings do jogo).

## Licença

MIT — ferramentas livres para uso pessoal. O conteúdo traduzido pertence aos criadores do OddSparks ([Massive Miniteam](https://www.massiveminiteam.com/)).
