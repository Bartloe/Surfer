# Changelog — Surfer

Alle noemenswaardige wijzigingen aan dit project staan hier (Nederlands).

## 2026-06-30

### Toegevoegd — stand-alone app (`app/`)
- Zelfstandige Surfer-app om per onderwerp (profiel) gericht **video's** te zoeken,
  ze door DeepSeek te laten beoordelen en de interessante treffers te bewaren.
- Staat los van BarTV; hergebruikt **ongewijzigd** het graafwerk uit `poc/`
  (pagina ophalen + tekst extraheren). Alle overige onderdelen zijn van de app zelf:
  - `graafwerk.py` — video-gericht zoeken (ddgs videos + text), video's uit pagina's halen.
  - `oordeel.py` — generiek DeepSeek-oordeel (sluit inhoud aan bij het profiel?).
  - `opslag.py` — profielen (`.txt` met Zoektermen/Context), resultaten + statussen +
    bezochte-urls-geheugen, schone export per profiel.
  - `kern.py` — orkestratie van één zoekronde (geheugen, suburls op een pagina).
  - `gui.py` — customtkinter-scherm: per blok pagina + suburls, aankruisvak, klikbare
    urls (openen = bezocht), oordeel rechts/samenvatting links, bulk-wissen.
  - `zelftest.py` — offline controle van de keten (geen kosten). Groen.
- Statussen: nieuw / bewaard / geskipt / bezocht. Bezochte urls vallen uit de export;
  geen url wordt twee keer opgehaald. Geen content-filters: alle sites bereikbaar.
