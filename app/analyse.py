"""
analyse — welke zoektermen leveren de beste (en slechtste) oogst voor een profiel.

Versie: 1.0
Reden:  Nieuw — per zoekterm samenvatten hoeveel vondsten zijn bewaard, weggegooid of
        nog open staan, plus de trefkans en het gemiddelde AI-cijfer. Zo zie je welke
        zoektermen veel bruikbaars opleveren en welke vooral ruis geven.
Datum:  2026-06-30 23:25 (NL)

- Pure rekenlaag: leest alleen opgeslagen vondsten en geeft een gesorteerde tabel
  terug (lijst van dicts). Geen web, geen scherm, geen schrijfacties.
- Per zoekterm (bron_term):
    * bewaard      : door jou aangevinkt (de keepers).
    * weggegooid   : bewust gewist (geskipt).
    * nieuw        : nog niet door jou bekeken.
    * trefkans     : bewaard / (bewaard + weggegooid) -> aandeel keepers van wat je
                     al beoordeelde; ontmaskert termen met veel ruis. None als je nog
                     niets beoordeelde.
    * gem_cijfer   : gemiddeld DeepSeek-cijfer over de écht beoordeelde vondsten
                     (video's en pagina's; geërfde suburl-cijfers tellen niet mee).
- Vondsten van vóór deze functie hebben geen herkomst en vallen onder '(onbekend)'.
- Sortering: meeste bewaard eerst, daarna hoogste trefkans.
"""

import opslag as opslag_mod

ONBEKEND = "(onbekend)"


def analyseer_profiel(naam: str) -> list[dict]:
    """Analyseer de opgeslagen vondsten van één profiel op naam."""
    winkel = opslag_mod.ProfielOpslag(naam)
    return analyseer(winkel.resultaten.values())


def analyseer(resultaten) -> list[dict]:
    """Groepeer vondsten per zoekterm en bereken de maatstaven. Zie de modulekop."""
    groepen: dict[str, dict] = {}
    for r in resultaten:
        term = (r.get("bron_term") or "").strip() or ONBEKEND
        g = groepen.setdefault(term, {
            "zoekterm": term, "bewaard": 0, "weggegooid": 0, "nieuw": 0,
            "totaal": 0, "_cijfer_som": 0.0, "_cijfer_n": 0,
        })
        g["totaal"] += 1
        status = r.get("status")
        if status == "bewaard":
            g["bewaard"] += 1
        elif status == "geskipt":
            g["weggegooid"] += 1
        elif status == "nieuw":
            g["nieuw"] += 1
        # Gemiddeld cijfer alleen over door DeepSeek écht beoordeelde vondsten
        # (die hebben een eigen oordeel-tekst; suburls erven enkel het paginacijfer).
        if (r.get("oordeel") or "").strip() and r.get("score"):
            g["_cijfer_som"] += float(r["score"])
            g["_cijfer_n"] += 1

    rijen: list[dict] = []
    for g in groepen.values():
        beoordeeld = g["bewaard"] + g["weggegooid"]
        g["trefkans"] = (g["bewaard"] / beoordeeld) if beoordeeld else None
        g["gem_cijfer"] = (g["_cijfer_som"] / g["_cijfer_n"]) if g["_cijfer_n"] else None
        del g["_cijfer_som"], g["_cijfer_n"]
        rijen.append(g)

    rijen.sort(key=lambda g: (g["bewaard"], g["trefkans"] or 0), reverse=True)
    return rijen
