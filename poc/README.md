# Surfer — ontdek-feeder

Surfer doorzoekt het web op nieuwe tv-series, schraapt de pagina's, haalt de
tekst eruit en laat DeepSeek een **goedkope, ruime voor-schifting** doen
(echte nieuwe serie? + grofweg passend bij een meegegeven profiel). De vondsten
gaan in een eigen, privé opslag.

## Kernregel (bewaakt de losweekbaarheid)

> **Uitvoer is het contract; de afnemer is onbekend en niet onze zaak.**

Surfer kent geen enkele afnemer. Alles wat hij nodig heeft — smaakprofiel,
zoektermen, uitsluitingen, opslaglocatie — komt als **gewoon functie-argument**
binnen (`SurferConfig`). Surfer leest nooit in een afnemer-bestand en bevat
nergens de naam of begrippen van een afnemer. Een geautomatiseerde check in de
zelftest faalt zodra dat tóch gebeurt.

## Draaien

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m surfer.runner --zelftest      # offline test
.venv\Scripts\python.exe -m surfer.runner start --max 5    # echte run (kost DeepSeek)
.venv\Scripts\python.exe -m surfer.runner status
.venv\Scripts\python.exe -m surfer.runner stop
.venv\Scripts\python.exe -m surfer.runner vondsten
```

De DeepSeek-sleutel komt uit `.env` (`DEEPSEEK_API_KEY=...`).

## Opbouw

| Module | Rol |
|---|---|
| `config.py` | alle invoer (`SurferConfig`), van buitenaf aan te reiken |
| `vondst.py` | de generieke uitvoervorm `Vondst` |
| `zoeken.py` | webzoeken (DuckDuckGo) |
| `scrapen.py` | pagina ophalen (requests) |
| `extractie.py` | tekst uit HTML (selectolax) |
| `beoordeling.py` | DeepSeek-voor-schifting (recall + grove smaak, meerdere per pagina) |
| `opslag.py` | de enige, privé SQLite-opslag (runs/vondsten/mislukt) |
| `pipeline.py` | de keten + start/stop/status |
| `runner.py` | opdrachtregel-ingang + zelftest |
