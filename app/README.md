# Surfer — stand-alone app

Een zelfstandige app om per **onderwerp** (profiel) gericht **video's** op het web
te vinden, ze door DeepSeek te laten beoordelen op aansluiting bij dat onderwerp,
en de interessante treffers te bewaren.

Deze app staat **los** van BarTV. Hij hergebruikt alleen het onderwerp-onafhankelijke
**graafwerk** van de bestaande Surfer (`../poc`: pagina ophalen + tekst eruit) en
verandert daar niets aan. Al het overige (video-zoeken, oordeel, profielen, opslag,
GUI) is van deze app zelf.

## Profielen

Een profiel is een gewoon tekstbestand in `profielen/<naam>.txt` met twee kopjes:

```
Zoektermen:
WK voetbal 2026 samenvatting
beste goals WK

Context:
Ik zoek video's met hoogtepunten en samenvattingen van recente
WK-voetbalwedstrijden. Bewegend beeld, geen losse nieuwsartikelen.
```

- **Zoektermen** — waarmee op het web gezocht wordt (één per regel).
- **Context** — beschrijft het onderwerp; DeepSeek beoordeelt elke treffer hiertegen.

## Draaien

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
copy .env.example .env          # en je DEEPSEEK_API_KEY invullen
.venv/Scripts/python.exe zelftest.py   # offline test, geen kosten
.venv/Scripts/python.exe gui.py        # de app
```

## Hoe het werkt

Per zoekterm zoekt de app (1) rechtstreeks naar video's en (2) naar webpagina's.
Pagina's worden opgehaald en door DeepSeek beoordeeld; sluit een pagina aan, dan
komen de video's die **erop** staan mee als **suburls** (ook zonder eigen info).
Alleen treffers die DeepSeek voldoende vindt (aansluiting + score ≥ drempel) worden
getoond. Geen content-filters: alle sites zijn bereikbaar.

## Statussen & opslag

Per profiel houdt `resultaten/<naam>.json` alles bij. Elke treffer heeft een status:

| Status | Betekenis | In de export? |
|---|---|---|
| nieuw | gevonden, nog niet afgehandeld | nee |
| bewaard | aangevinkt | **ja** |
| geskipt | weggeklikt (los of per blok/run) | nee |
| bezocht | url geopend → afgehandeld | nee |

- Klik je een url aan, dan opent hij in je browser en wordt hij **bezocht** (valt uit
  de export). Elke url die ooit gevonden is, wordt **nooit opnieuw** opgehaald.
- `resultaten/<naam>_bewaard.json` is de schone oogst: alleen de bewaarde urls.
- Bulk: **wis blok** (een pagina + haar suburls) en **wis alles van laatste run**.

## Opbouw

| Bestand | Laag | Rol |
|---|---|---|
| `graafwerk.py` | web | zoeken + (gedeeld) ophalen/extraheren + video's uit pagina's |
| `oordeel.py` | logica | generiek DeepSeek-oordeel (past inhoud bij profiel?) |
| `opslag.py` | data | profielen lezen + resultaten/statussen/geheugen (json) |
| `kern.py` | logica | de orkestratie van één zoekronde |
| `gui.py` | UI | het customtkinter-scherm |
| `zelftest.py` | test | offline controle van de keten |
