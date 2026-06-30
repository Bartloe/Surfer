"""
kern — orkestratie van één zoekronde voor een profiel.

Versie: 1.0
Reden:  Eerste versie — koppelt graafwerk + DeepSeek-oordeel + opslag tot één run.
Datum:  2026-06-30 19:18 (NL)

Per run, per zoekterm:
  1. directe video's zoeken  -> elk apart door DeepSeek laten beoordelen;
  2. webpagina's zoeken      -> ophalen + beoordelen; bij aansluiting komen de
     video's die OP die pagina staan als suburls mee (ook zonder eigen info).
Al-geziene urls worden overgeslagen (geheugen per profiel). Alleen treffers die
DeepSeek voldoende vindt (past + score >= drempel) worden bewaard als resultaat.
Logt per stap een korte samenvatting; faalt zacht per item.
"""

import os
from datetime import datetime

from dotenv import load_dotenv

import graafwerk
import opslag as opslag_mod
from oordeel import DeepSeekOordeel


def maak_oordelaar():
    """Bouwt de DeepSeek-beoordelaar uit .env. Aparte functie -> testbaar/vervangbaar."""
    load_dotenv(opslag_mod.BASIS / ".env")
    return DeepSeekOordeel(os.getenv("DEEPSEEK_API_KEY", ""),
                           os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))


def run(profiel: str, *, drempel: float = 6.0, max_per_term: int = 12,
        oordelaar=None, log=print, voortgang=None, stop=None) -> dict:
    """Draait één zoekronde. Geeft een korte samenvatting terug."""
    zoektermen, context = opslag_mod.lees_profiel(profiel)
    if not zoektermen:
        log(f"[surf] profiel '{profiel}': geen zoektermen gevonden.")
        return {"nieuw": 0, "fout": "geen zoektermen"}

    winkel = opslag_mod.ProfielOpslag(profiel)
    oordelaar = oordelaar or maak_oordelaar()
    run_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"[surf] run {run_id} — profiel '{profiel}', {len(zoektermen)} zoekterm(en)")

    nieuw = 0
    try:
        for i, term in enumerate(zoektermen, 1):
            if stop and stop():
                log("[surf] gestopt op verzoek.")
                break
            if voortgang:
                voortgang(i, len(zoektermen), term)

            # 1) directe video-treffers
            for t in graafwerk.zoek_videos(term, max_per_term):
                if stop and stop():
                    break
                if winkel.is_gezien(t.url):
                    continue
                winkel.markeer_gezien(t.url)
                res = oordelaar.beoordeel(t.titel, t.fragment, context)
                if res["past"] and res["score"] >= drempel:
                    winkel.voeg_resultaat(t.url, t.titel, "video", run_id,
                                          res["samenvatting"], res["oordeel"], res["score"])
                    nieuw += 1

            # 2) webpagina's -> video's eraf halen
            for p in graafwerk.zoek_paginas(term, max_per_term):
                if stop and stop():
                    break
                if winkel.is_gezien(p.url):
                    continue
                winkel.markeer_gezien(p.url)
                pagina = graafwerk.haal_pagina(p.url)
                if pagina["fout"]:
                    continue
                res = oordelaar.beoordeel(pagina["titel"] or p.titel, pagina["tekst"], context)
                if not (res["past"] and res["score"] >= drempel):
                    continue
                winkel.voeg_resultaat(p.url, pagina["titel"] or p.titel, "pagina", run_id,
                                      res["samenvatting"], res["oordeel"], res["score"])
                nieuw += 1
                for v in graafwerk.videos_op_pagina(pagina["html"], p.url):
                    if winkel.is_gezien(v.url):
                        continue
                    winkel.markeer_gezien(v.url)
                    winkel.voeg_resultaat(v.url, v.titel, "suburl", run_id,
                                          "(video gevonden op de bovenstaande pagina)",
                                          "", res["score"], parent_url=p.url)
                    nieuw += 1
    finally:
        winkel.bewaar()

    log(f"[surf] run {run_id} klaar: {nieuw} nieuwe treffer(s).")
    return {"nieuw": nieuw, "run": run_id}
