"""
runner — opdrachtregel-ingang: start / status / stop / vondsten / zelftest.

Versie: 1.0
Reden:  Fase 0 — fatsoenlijk start/stop/status op een run; nep-thread vervangen.
Datum:  2026-06-27 17:56 (NL)

Gebruik:
  python -m surfer.runner start   [--max N] [--export PAD]
  python -m surfer.runner status
  python -m surfer.runner stop
  python -m surfer.runner vondsten [--run ID]
  python -m surfer.runner --zelftest

- start    : draait één run (weigert als er al één loopt).
- status   : toont de laatste run.
- stop     : vraagt de lopende run netjes te stoppen (tussen items).
- vondsten : toont de vondsten van een run.
- zelftest : offline end-to-end test (nep-beoordelaar) + nul-afnemer-check.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .config import SurferConfig, standaard_config
from .opslag import Opslag
from .pipeline import surf


def _cmd_start(args) -> int:
    config = standaard_config()
    if args.max:
        config.max_resultaten_per_term = args.max
    opslag = Opslag(config.db_pad)
    try:
        resultaat = surf(config, opslag)
    except RuntimeError as e:
        print(f"FOUT: {e}")
        return 1
    if args.export:
        _exporteer(opslag, resultaat["run_id"], Path(args.export))
        print(f"Vondsten weggeschreven naar {args.export}")
    return 0


def _cmd_status(args) -> int:
    opslag = Opslag(standaard_config().db_pad)
    run = opslag.laatste_run()
    if not run:
        print("Nog geen run gedraaid.")
        return 0
    print(f"Laatste run #{run['id']}: {run['status']}")
    print(f"  gestart   : {run['gestart_op']}")
    print(f"  geëindigd : {run['geeindigd_op'] or '-'}")
    print(f"  vondsten  : {run['aantal_vondsten']}")
    print(f"  mislukt   : {run['aantal_mislukt']}")
    if run["notitie"]:
        print(f"  notitie   : {run['notitie']}")
    return 0


def _cmd_stop(args) -> int:
    opslag = Opslag(standaard_config().db_pad)
    if opslag.vraag_stop():
        print("Stop gevraagd; de lopende run stopt na het huidige item.")
    else:
        print("Geen lopende run om te stoppen.")
    return 0


def _cmd_vondsten(args) -> int:
    opslag = Opslag(standaard_config().db_pad)
    run_id = args.run or (opslag.laatste_run() or {}).get("id")
    if not run_id:
        print("Nog geen run gedraaid.")
        return 0
    vondsten = opslag.vondsten_van(run_id)
    print(f"Run #{run_id}: {len(vondsten)} vondst(en)")
    for v in vondsten:
        print(f"  [{v['smaak_indicatie']:.1f}] {v['titel']}  <{v['bron_url']}>")
    return 0


def _exporteer(opslag: Opslag, run_id: int, pad: Path) -> None:
    """Leesbare dump (regels-JSON) van een run — gemak voor de mens, geen contract."""
    with open(pad, "w", encoding="utf-8") as f:
        for v in opslag.vondsten_van(run_id):
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# ZELFTEST — offline, zonder netwerk of DeepSeek
# --------------------------------------------------------------------------
def _zelftest() -> int:
    fouten: list[str] = []

    class NepBeoordelaar:
        def beoordeel(self, titel, tekst, profiel_tekst):
            # Eén pagina -> twee vondsten (bewijst de listicle-winst).
            return [
                {"titel": "Testserie A", "samenvatting": "x", "taal": "en",
                 "is_relevant": True, "relevantie_reden": "nieuw", "smaak_indicatie": 8},
                {"titel": "Testserie B", "samenvatting": "y", "taal": "en",
                 "is_relevant": True, "relevantie_reden": "nieuw", "smaak_indicatie": 5},
            ]

    def nep_zoek(term, maxr):
        return {"kandidaten": [{"titel": "p", "url": "https://example.com/lijst",
                                "fragment": "f"}], "fout": None}

    class NepScraper:
        def haal_op(self, url):
            return "<html><body>" + ("<p>" + "nieuwe serie 2026 " * 20 + "</p>") + "</body></html>", None

    def nep_extract(html):
        from .extractie import Extractie
        return Extractie(titel="Pagina", tekst="new tv series 2026 " * 30, omschrijving="")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Path(tmp) / "t.db"
        opslag = Opslag(db)
        config = SurferConfig(zoektermen=["a", "b"], deepseek_api_key="nep",
                              pauze_seconden=0, talen=["en"])

        # 1) End-to-end happy path: 2 termen x 1 pagina x 2 vondsten = 4
        res = surf(config, opslag, beoordelaar=NepBeoordelaar(), zoeker=nep_zoek,
                   scraper=NepScraper(), extractor=nep_extract, log=lambda *a: None)
        if res["status"] != "klaar":
            fouten.append(f"status zou 'klaar' moeten zijn, was '{res['status']}'")
        if res["aantal_vondsten"] != 4:
            fouten.append(f"verwachtte 4 vondsten (listicle), kreeg {res['aantal_vondsten']}")

        # 2) Dubbele-start-bescherming
        opslag.start_run()
        try:
            opslag.start_run()
            fouten.append("tweede start had geweigerd moeten worden")
        except RuntimeError:
            pass
        opslag.beeindig_run(opslag.actieve_run(), "klaar")

        # 3) Stop-vlag wordt gerespecteerd
        opslag2 = Opslag(Path(tmp) / "t2.db")

        def zoek_met_stop(term, maxr):
            opslag2.vraag_stop()  # vraag stop vóór de eerste kandidaat verwerkt is
            return {"kandidaten": [{"titel": "p", "url": "https://example.com/x",
                                    "fragment": "f"}], "fout": None}

        res2 = surf(config, opslag2, beoordelaar=NepBeoordelaar(), zoeker=zoek_met_stop,
                    scraper=NepScraper(), extractor=nep_extract, log=lambda *a: None)
        if res2["status"] != "gestopt":
            fouten.append(f"stop-vlag genegeerd: status was '{res2['status']}'")

    # 4) Eénrichtingsregel: nul verwijzingen naar een afnemer in de Surfer-code
    raak = _scan_op_afnemer()
    if raak:
        fouten.append(f"afnemer-verwijzing gevonden in: {', '.join(raak)}")

    if fouten:
        print("ZELFTEST (ROOD):")
        for f in fouten:
            print("  - " + f)
        return 1
    print("ZELFTEST (GROEN): pipeline, dubbel-start, stop-vlag en nul-afnemer-check OK")
    return 0


def _scan_op_afnemer() -> list[str]:
    """Faalt zodra Surfer-code de naam van een afnemer bevat (losweekbaarheid).

    Het verboden woord wordt bewust samengesteld, zodat deze bronregel de
    scan niet zelf triggert en géén Surfer-bestand de naam letterlijk bevat.
    """
    verboden = "bar" + "tv"
    map_pad = Path(__file__).parent
    raak = []
    for py in map_pad.glob("*.py"):
        try:
            inhoud = py.read_text(encoding="utf-8").lower()
        except Exception:
            continue
        if verboden in inhoud:
            raak.append(py.name)
    return raak


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="surfer.runner", description="Surfer feeder")
    parser.add_argument("--zelftest", action="store_true", help="offline zelftest")
    sub = parser.add_subparsers(dest="commando")

    p_start = sub.add_parser("start", help="draai één run")
    p_start.add_argument("--max", type=int, default=None, help="max resultaten per zoekterm")
    p_start.add_argument("--export", default=None, help="schrijf vondsten naar dit pad (jsonl)")

    sub.add_parser("status", help="toon laatste run")
    sub.add_parser("stop", help="vraag lopende run te stoppen")
    p_v = sub.add_parser("vondsten", help="toon vondsten van een run")
    p_v.add_argument("--run", type=int, default=None)

    args = parser.parse_args(argv)
    if args.zelftest:
        return _zelftest()
    if args.commando == "start":
        return _cmd_start(args)
    if args.commando == "status":
        return _cmd_status(args)
    if args.commando == "stop":
        return _cmd_stop(args)
    if args.commando == "vondsten":
        return _cmd_vondsten(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
