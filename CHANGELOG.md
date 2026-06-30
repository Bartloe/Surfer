# Changelog — Surfer

Alle noemenswaardige wijzigingen aan dit project staan hier (Nederlands).

## 2026-07-01 (nacht) — lange url verbergt de score niet meer (`app/` gui.py v1.9)

### Opgelost — score blijft zichtbaar + overbodige knop weg
- Bij een lange titel/url verdween de score onder de 'kopieer'-knop en werd die knop
  in elkaar gedrukt. De score wordt nu **rechts in de regel vastgepind** (eerst
  geplaatst), zodat de titel alleen de ruimte ertussen vult en de score altijd in beeld
  blijft.
- De **'kopieer'-knop is verwijderd** (hoofd- en subregels): hij was een overblijfsel van
  vóór het titel-keuzemenu, dat al 'URL kopiëren' bevat. De `_kopieer`-functie blijft
  bestaan voor dat menu.

## 2026-07-01 (nacht) — bewaarde vondsten naar een eigen scherm (`app/` gui.py v1.8)

### Gewijzigd — Resultaten en Bewaard gescheiden
- Het resultatenscherm liep op den duur vol met een steeds groeiend bewaard-blok
  bovenaan, waardoor de nieuwe (nog te beoordelen) vondsten werden weggeduwd.
- **Twee tabs op de weergavebalk** (`gui.py` v1.8): *Resultaten* toont alléén de nieuwe
  vondsten (in batches); *Bewaard (N)* toont alléén je keepers op een eigen scherm. De
  teller op de tab loopt meteen mee bij elk aan-/uitvinken.
- Een vondst die je aanvinkt blijft op het Resultaten-scherm staan tot je verder gaat
  (volgende run, bladeren of van tab wisselen) — zo verspringt de lijst niet onder je
  muis. Op het Bewaard-scherm haal je iets weer uit bewaard door het uit te vinken.
- De batch-navigatie en de bulk-wisknoppen horen bij Resultaten en staan op het
  Bewaard-scherm uit. Alleen `gui.py` aangepast; de datalaag is ongemoeid.

## 2026-06-30 (nacht) — zoekterm-analyse (welke termen leveren het meeste op)

### Nieuw — analyse van de zoektermen
- **Herkomst vastgelegd** (`opslag.py` v1.2, `kern.py` v1.2): elke vondst onthoudt nu
  via welke zoekterm hij binnenkwam (`bron_term`); video's van een pagina erven de term
  van die pagina. *Let op:* dit meet vanaf nu — vondsten van vóór deze wijziging hebben
  geen herkomst en vallen onder "(onbekend)".
- **Rekenlaag** (`analyse.py` v1.0): vat de vondsten samen per zoekterm — bewaard,
  weggegooid, nog open, **trefkans** (bewaard ÷ beoordeeld → ontmaskert ruis-termen) en
  het **gemiddelde AI-cijfer** over de écht beoordeelde vondsten. Gesorteerd op meeste
  bewaard.
- **Los rapport** (`rapport_zoektermen.py` v1.0): `python rapport_zoektermen.py <profiel>`
  toont de tabel op het scherm en bewaart 'm als `resultaten/<profiel>_zoektermen.txt`.
- **Knop in de app** (`gui.py` v1.7): *Analyse zoektermen* (rechts op de weergavebalk)
  opent een venster met dezelfde tabel voor het gekozen profiel.
- **Zelftest** (`zelftest.py` v1.2): test op telling per zoekterm, trefkans, gemiddeld
  cijfer, sortering en de "(onbekend)"-groep.

## 2026-06-30 (nacht) — oordeel naast titel + meegroeiende breedte (`app/` gui.py v1.6)

### Gewijzigd — AI-oordeel begint nu echt op titelhoogte
- Het oordeel stond rechts, maar begon op de url-regel — een regel onder de titel. Het
  staat nu rechts náást het hele linkerblok (titel + url + samenvatting) en begint
  bovenaan, op dezelfde hoogte als de titel.

### Gewijzigd — tekst benut de volle breedte bij een groot venster
- De url-beschrijving en het oordeel hadden een vaste regelbreedte (440px); bij een
  volledig scherm bleef rechts veel ruimte leeg. De regelbreedte groeit nu mee met het
  venster, zodat beide panelen volledig benut worden.

## 2026-06-30 (laat) — keuzemenu op url + compacter oordeel (`app/` gui.py v1.4)

### Gewijzigd — klikken op een titel geeft nu een keuzemenu
- Een titel openen ging direct naar de browser. Nu verschijnt een klein keuzemenu met
  **Openen in browser**, **Openen in privévenster** (Chrome incognito of Edge InPrivate)
  en **URL kopiëren**. Geldt voor zowel de pagina-titels als de losse video-regels.

### Gewijzigd — AI-oordeel begint hoger
- Het DeepSeek-oordeel (rechterkolom) begon onder de url-regel en kostte daardoor extra
  hoogte per serie. De url staat nu bovenin de linkerkolom en het oordeel begint op
  **dezelfde hoogte** — zo neemt elke vondst minder regels in beslag.

## 2026-06-30 (avond) — indeling + titels uit tabellen

### Gewijzigd — schermindeling op verzoek (`app/` gui.py v1.3)
- **Sorteren + Per batch** staan nu **bovenaan** (eigen weergavebalk onder de zoekbalk).
- **Bladeren** (*◀ Vorige* / *Volgende ▶*) en de teller staan nu **rechtsonder**.
- **Per regel:** *wis* staat links (naast *bewaar*); *kopieer* staat direct rechts van
  de titel. Het oordeel-cijfer staat uiterst rechts.
- **Live verloop** verschijnt alleen tijdens een zoekronde en verdwijnt zodra de
  resultaten klaarstaan. Bewust géén live bijwerken tijdens de run: dat zou met
  sorteren-op-score onrustig heen-en-weer springen.

### Opgelost — video-titels op tabelpagina's (`app/` graafwerk.py v1.2)
- Pagina's als de Ziggo-samenvattingen zetten per wedstrijd een "YouTube"-knop in een
  tabelrij; de échte titel (de wedstrijd) staat in een náástliggende cel. Voorheen
  kreeg daardoor maar één van de ~76 video's een titel en toonde de rest "YouTube".
  Nu wordt de titel uit de rij (of uit een kop/onderschrift) gehaald, en tellen
  labels als "YouTube"/"Vimeo" niet meer als titel. Resultaat: alle 76 video's
  krijgen hun wedstrijdnaam.

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
