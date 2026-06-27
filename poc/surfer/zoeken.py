"""
zoeken — webzoekstap (DuckDuckGo).

Versie: 1.0
Reden:  Fase 0 — enige zoek-engine; dode Brave/Google-engines verwijderd.
Datum:  2026-06-27 17:56 (NL)

- zoek() geeft per zoekterm een lijst kandidaten (titel, url, fragment).
- Faalt zacht: een mislukte zoekopdracht levert een lege lijst + reden,
  zodat de pipeline doorloopt i.p.v. te crashen.
"""

from ddgs import DDGS


def zoek(query: str, max_resultaten: int = 10) -> dict:
    try:
        with DDGS() as ddgs:
            ruw = list(ddgs.text(query, max_results=max_resultaten))
        kandidaten = [
            {
                "titel": r.get("title", ""),
                "url": r.get("href", ""),
                "fragment": r.get("body", ""),
            }
            for r in ruw
        ]
        return {"kandidaten": kandidaten, "fout": None}
    except Exception as e:
        return {"kandidaten": [], "fout": str(e)}
