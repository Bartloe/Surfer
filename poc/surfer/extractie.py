"""
extractie — leesbare tekst uit ruwe HTML halen.

Versie: 1.0
Reden:  Fase 0 — één extractor (selectolax); registry/AI-extractors verwijderd.
Datum:  2026-06-27 17:56 (NL)

- extraheer() haalt titel, meta-omschrijving en hoofdtekst uit een pagina.
- Verwijdert ruis (script/nav/footer) en plakt zinvolle paragrafen samen.
- Geeft None terug bij lege/onbruikbare HTML, zodat de pipeline kan overslaan.
"""

import re
from dataclasses import dataclass

from selectolax.parser import HTMLParser


@dataclass
class Extractie:
    titel: str
    tekst: str
    omschrijving: str


def extraheer(html: str) -> Extractie | None:
    if not html or len(html.strip()) < 50:
        return None

    boom = HTMLParser(html)

    titel = ""
    titel_tag = boom.css_first("title")
    if titel_tag:
        titel = titel_tag.text().strip()
    og_titel = boom.css_first("meta[property='og:title']")
    if og_titel and og_titel.attributes.get("content"):
        titel = og_titel.attributes["content"].strip()

    omschrijving = ""
    desc = boom.css_first("meta[name='description']")
    if desc and desc.attributes.get("content"):
        omschrijving = desc.attributes["content"].strip()
    og_desc = boom.css_first("meta[property='og:description']")
    if og_desc and og_desc.attributes.get("content"):
        omschrijving = og_desc.attributes["content"].strip()

    tekst = _hoofdtekst(boom)
    return Extractie(titel=titel, tekst=tekst, omschrijving=omschrijving)


def _hoofdtekst(boom: HTMLParser) -> str:
    for selector in ["script", "style", "nav", "footer", "header", "noscript"]:
        for tag in boom.css(selector):
            tag.decompose()

    paragrafen = [p.text().strip() for p in boom.css("p") if len(p.text().strip()) > 40]
    if not paragrafen:
        artikel = boom.css_first("article")
        if artikel:
            return _opschonen(artikel.text().strip())
    return _opschonen("\n".join(paragrafen))


def _opschonen(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst).strip()
