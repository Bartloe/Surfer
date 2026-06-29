"""
pipeline — de keten: zoeken -> scrapen -> extraheren -> beoordelen -> opslaan.

Versie: 1.1
Reden:  Binnen-run URL-dedup — verwante zoektermen leveren vaak dezelfde pagina op;
        die nu één keer scrapen + beoordelen i.p.v. dubbel (kostenbesparing). Tussen
        runs blijft herbezoek toegestaan (een pagina kan later nieuwe series tonen).
Datum:  2026-06-29 (NL)
Vorige: 1.0 (2026-06-27) — Fase 0: één heldere orkestratie i.p.v. een rauwe thread.

- surf() draait precies één run en geeft een korte samenvatting terug.
- Alle bouwstenen zijn injecteerbaar (zoeker/scraper/extractor/beoordelaar):
  zo is de keten testbaar én kan een afnemer eigen onderdelen meegeven.
- Respecteert de stop-vlag: tussen items checkt hij of stoppen gevraagd is.
- Logt per stap een korte in/uit-samenvatting; faalt zacht per item.
"""

import time

from .beoordeling import DeepSeekBeoordelaar
from .config import SurferConfig
from .extractie import extraheer as _extraheer
from .opslag import Opslag
from .scrapen import Scraper
from .vondst import Vondst
from .zoeken import zoek as _zoek


def _taal_ok(tekst: str, talen: list[str], drempel: int) -> bool:
    if len(tekst) < drempel:
        return False
    try:
        from langdetect import detect
        return detect(tekst) in talen
    except Exception:
        return True  # bij twijfel insluiten (recall)


def surf(config: SurferConfig, opslag: Opslag, *, beoordelaar=None,
         zoeker=None, scraper=None, extractor=None, log=print) -> dict:
    zoeker = zoeker or _zoek
    scraper = scraper or Scraper()
    extractor = extractor or _extraheer
    if beoordelaar is None:
        beoordelaar = DeepSeekBeoordelaar(config.deepseek_api_key, config.deepseek_model)

    run_id = opslag.start_run()
    log(f"[surf] run {run_id} gestart — {len(config.zoektermen)} zoekterm(en)")
    gestopt = False
    # URL's die deze run al verwerkt zijn — verwante zoektermen leveren vaak dezelfde
    # pagina op. Eén keer scrapen + door DeepSeek laten beoordelen i.p.v. per zoekterm
    # opnieuw scheelt direct in kosten. Geldt binnen één run; tussen runs (her)bezoeken
    # mag juist wél (een pagina kan later nieuwe series tonen).
    bezocht: set[str] = set()
    overgeslagen = 0
    try:
        for term in config.zoektermen:
            if opslag.stop_gevraagd(run_id):
                gestopt = True
                break
            resultaat = zoeker(term, config.max_resultaten_per_term)
            kandidaten = resultaat["kandidaten"]
            log(f"[surf] zoekterm '{term}': {len(kandidaten)} kandidaten"
                + (f" (zoekfout: {resultaat['fout']})" if resultaat["fout"] else ""))

            for kandidaat in kandidaten:
                if opslag.stop_gevraagd(run_id):
                    gestopt = True
                    break
                url = (kandidaat.get("url") or "").strip()
                if url and url in bezocht:
                    overgeslagen += 1
                    continue                       # deze run al gehad — niet dubbel scrapen
                if url:
                    bezocht.add(url)
                _verwerk_kandidaat(kandidaat, run_id, config, opslag,
                                   scraper, extractor, beoordelaar, log)
                time.sleep(config.pauze_seconden)
            if gestopt:
                break
    except Exception as e:
        opslag.beeindig_run(run_id, "fout", str(e))
        log(f"[surf] run {run_id} GESTOPT door fout: {e}")
        raise

    status = "gestopt" if gestopt else "klaar"
    opslag.beeindig_run(run_id, status)
    samenvatting = opslag.laatste_run() or {}
    log(f"[surf] run {run_id} {status}: "
        f"{samenvatting.get('aantal_vondsten', 0)} vondsten, "
        f"{samenvatting.get('aantal_mislukt', 0)} mislukt"
        + (f", {overgeslagen} dubbele URL('s) overgeslagen" if overgeslagen else ""))
    return {
        "run_id": run_id,
        "status": status,
        "aantal_vondsten": samenvatting.get("aantal_vondsten", 0),
        "aantal_mislukt": samenvatting.get("aantal_mislukt", 0),
    }


def _verwerk_kandidaat(kandidaat, run_id, config, opslag,
                       scraper, extractor, beoordelaar, log):
    url = kandidaat.get("url")
    if not url:
        return
    if any(domein in url for domein in config.verboden_domeinen):
        return

    html, fout = scraper.haal_op(url)
    if fout:
        opslag.bewaar_mislukt(run_id, url, f"scrape: {fout}")
        return

    extractie = extractor(html)
    if extractie is None:
        opslag.bewaar_mislukt(run_id, url, "extractie: geen bruikbare tekst")
        return

    if not _taal_ok(extractie.tekst, config.talen, config.min_tekst_voor_taaldetectie):
        return

    try:
        rauwe = beoordelaar.beoordeel(extractie.titel or kandidaat.get("titel", ""),
                                      extractie.tekst, config.profiel_tekst)
    except Exception as e:
        opslag.bewaar_mislukt(run_id, url, f"beoordeling: {e}")
        return

    for r in rauwe:
        titel = (r.get("titel") or "").strip()
        if not titel:
            continue
        opslag.bewaar_vondst(run_id, Vondst(
            titel=titel,
            bron_url=url,
            samenvatting=r.get("samenvatting", ""),
            taal=r.get("taal", ""),
            relevantie_reden=r.get("relevantie_reden", ""),
            is_relevant=bool(r.get("is_relevant", True)),
            smaak_indicatie=float(r.get("smaak_indicatie", 0) or 0),
        ))
