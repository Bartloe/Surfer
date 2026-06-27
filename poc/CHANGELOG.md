# Changelog — Surfer

Alle noemenswaardige wijzigingen aan Surfer staan hier (Nederlands).

## [Fase 0] 2026-06-27 — Opgeschoond tot een schone, losweekbare feeder

Surfer is van proefversie teruggebracht tot één heldere feeder. Niets van de
oude losse-eindjes is blijven staan; de werkende kern (DuckDuckGo-zoeken en
HTML-extractie) is schoon herbouwd.

### Toegevoegd
- Nieuw, generiek `surfer`-pakket met gescheiden stappen: `config`, `vondst`,
  `zoeken`, `scrapen`, `extractie`, `beoordeling`, `opslag`, `pipeline`, `runner`.
- Alle invoer komt van buitenaf via `SurferConfig` (smaakprofiel, zoektermen,
  uitsluitingen, talen, opslaglocatie) — niets meer hardcoded of uit een db.
- DeepSeek-beoordeling herschreven: een **goedkope, ruime voor-schifting**
  (echte nieuwe serie? + grofweg passend bij het profiel) die **meerdere
  vondsten per pagina** teruggeeft (listicles), zonder harde smaak-poort.
- Eén privé SQLite-opslag met fatsoenlijk **start/stop/status** op een run,
  inclusief bescherming tegen dubbel starten.
- `runner` als opdrachtregel-ingang: `start` / `status` / `stop` / `vondsten`
  en een offline `--zelftest`.
- Geautomatiseerde **eénrichtingscheck**: de zelftest faalt zodra Surfer-code
  de naam van een afnemer bevat. Bewaakt dat Surfer losweekbaar blijft.
- `requirements.txt` + schone `.venv`.

### Verwijderd
- Drie door elkaar lopende db-lagen (`db`, `db_sync`, `storage`).
- Ongebruikte zoek-engines (Brave, Google-HTML) en headless scraper (Playwright).
- Wees-subsysteem (`results`/`models`/`exporter`/`analyzer`/`taste_profiles`).
- Kapotte `config.py` (pydantic v1 BaseSettings) en de migratierunner.
- Het FastAPI-dashboard met templates/static (het triage-scherm verhuist naar
  de afnemer-kant; een feeder heeft zelf geen UI nodig).

### Opgelost
- SQLite-verbindingen werden nooit gesloten (`with` op een connectie commit
  alleen), waardoor het db-bestand op Windows vergrendeld bleef. Verbindingen
  sluiten nu altijd via een eigen context-manager.
