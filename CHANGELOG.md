# Changelog — Surfer

Alle noemenswaardige wijzigingen aan dit project staan hier (Nederlands).

## 2026-06-30

### Toegevoegd — overzicht bij veel vondsten + dubbelklik-start (`app/` gui.py v1.2)
- **Sorteerknop:** vondsten sorteren op *Hoogste score* of *Laatste run*.
- **Batch-weergave:** niet meer alles tegelijk, maar N per keer (instelbaar, standaard 25)
  met *◀ Vorige* / *Volgende ▶* en een teller "Toont X–Y van Z". Knop
  **"Wis getoonde (niet-bewaard)"** gooit de zichtbare, niet-aangevinkte vondsten weg en
  schuift de volgende batch in beeld — zo werk je in hapklare brokken door een grote oogst.
- **Bewaarde vondsten** staan nu apart bovenaan ("✅ Bewaard (N)") en blijven altijd in
  beeld; ze tellen niet mee in de te-beoordelen batches.
- **start.bat:** de app starten met een dubbelklik (geen terminal meer nodig).

### Gewijzigd — stand-alone app (`app/`), eerste gebruikersronde
- **Live verloop:** nieuw venster onder de knoppen dat tijdens een run per stap
  toont wat er gebeurt (zoeken, ophalen, beoordelen, bewaard, valt af). Voorheen
  zag je alleen "Bezig…". (`kern.py` v1.1 logt per stap, `gui.py` v1.1 toont het.)
- **Aanklikken wist niets meer:** een url openen is bladeren — de browser opent en
  de regel blijft staan. Weghalen doe je bewust met *wis* of *wis hele pagina*.
  (De status 'bezocht' verdwijnt daarmee uit het gedrag.)
- **Kopieer-knop** per regel: url naar het klembord (naast aanklikken).
- **Betere video-titels** van rijke pagina's (bv. Ziggo-samenvattingen): de echte
  omschrijving komt nu uit aria-label/title/alt; een kaal label "video" valt weg en
  toont anders de url. (`graafwerk.py` v1.1.)
- **Compacte video-regels:** elke video onder een pagina (en losse weesvideo's) staat
  nu op één strakke regel i.p.v. een groot blok.
- 'wis blok' heet nu **'wis hele pagina'** (duidelijker: pagina + de video's erop).

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
