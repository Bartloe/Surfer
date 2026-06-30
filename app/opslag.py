"""
opslag — datalaag: profielen lezen + per-profiel resultaten/statussen/geheugen.

Versie: 1.2
Reden:  Herkomst vastleggen — elk resultaat onthoudt nu via welke zoekterm het
        binnenkwam ('bron_term'). Hierop draait de zoekterm-analyse (welke termen
        leveren de meeste bewaarde vondsten). Oude vondsten zonder dit veld tellen
        als 'onbekend'. Eerder (v1.1): veilig wegschrijven + .bak-reservekopie.
Datum:  2026-06-30 23:25 (NL)

- Profiel = los .txt-bestand in profielen/ met de kopjes 'Zoektermen:' en 'Context:'.
- Per profiel één werkbestand resultaten/<profiel>.json met:
    * gezien_urls : elke url die ooit is opgehaald/getoond -> nooit 2x bezoeken.
    * resultaten  : alle vondsten met hun status.
- Statussen: 'nieuw' (te beoordelen), 'bewaard' (aangevinkt), 'geskipt' (weg).
  Aanklikken opent alleen de browser en verandert de status NIET; weghalen gaat
  bewust via 'wis' (één regel) of 'wis hele pagina' (pagina + video's erop).
- Bij elke opslag wordt resultaten/<profiel>_bewaard.json ververst: de schone
  oogst met alleen de bewaarde, nog niet bezochte urls (de "export").
- Een resultaat met type 'suburl' hoort bij een pagina via parent_url; pagina +
  suburls vormen samen één blok (voor bulk-wissen).
"""

import json
from datetime import datetime
from pathlib import Path

BASIS = Path(__file__).resolve().parent
PROFIELEN_MAP = BASIS / "profielen"
RESULTATEN_MAP = BASIS / "resultaten"


# ----------------------------------------------------------------------------- profielen
def lijst_profielen() -> list[str]:
    PROFIELEN_MAP.mkdir(exist_ok=True)
    return sorted(p.stem for p in PROFIELEN_MAP.glob("*.txt"))


def profiel_pad(naam: str) -> Path:
    return PROFIELEN_MAP / f"{naam}.txt"


def lees_profiel(naam: str) -> tuple[list[str], str]:
    """Geeft (zoektermen, context) uit een profiel-.txt. Faalt zacht bij ontbreken."""
    pad = profiel_pad(naam)
    if not pad.exists():
        return [], ""
    zoektermen: list[str] = []
    context_regels: list[str] = []
    sectie = None
    for regel in pad.read_text(encoding="utf-8").splitlines():
        kop = regel.strip().lower()
        if kop.startswith("zoektermen:"):
            sectie = "zoek"
            rest = regel.split(":", 1)[1].strip()
            if rest:
                zoektermen.append(rest)
        elif kop.startswith("context:"):
            sectie = "context"
            rest = regel.split(":", 1)[1].strip()
            if rest:
                context_regels.append(rest)
        elif sectie == "zoek":
            if regel.strip():
                zoektermen.append(regel.strip())
        elif sectie == "context":
            context_regels.append(regel)
    return zoektermen, "\n".join(context_regels).strip()


# ----------------------------------------------------------------------------- resultaten
class ProfielOpslag:
    def __init__(self, naam: str):
        self.naam = naam
        RESULTATEN_MAP.mkdir(exist_ok=True)
        self.pad = RESULTATEN_MAP / f"{naam}.json"
        self.export_pad = RESULTATEN_MAP / f"{naam}_bewaard.json"
        self.gezien: set[str] = set()
        self.resultaten: dict[str, dict] = {}
        self._laad()

    def _laad(self):
        if not self.pad.exists():
            return
        try:
            data = json.loads(self.pad.read_text(encoding="utf-8"))
            self.gezien = set(data.get("gezien_urls", []))
            for r in data.get("resultaten", []):
                self.resultaten[r["url"]] = r
        except Exception:
            pass  # corrupt/leeg bestand: schoon beginnen, oude wordt overschreven

    # -- geheugen ------------------------------------------------------------
    def is_gezien(self, url: str) -> bool:
        return url in self.gezien

    def markeer_gezien(self, url: str):
        if url:
            self.gezien.add(url)

    # -- toevoegen / wijzigen ------------------------------------------------
    def voeg_resultaat(self, url: str, titel: str, type: str, run: str,
                       samenvatting: str = "", oordeel: str = "", score: float = 0.0,
                       parent_url: str | None = None, bron_term: str | None = None):
        if url in self.resultaten:
            return
        self.resultaten[url] = {
            "url": url, "titel": titel, "type": type, "run": run,
            "samenvatting": samenvatting, "oordeel": oordeel, "score": score,
            "parent_url": parent_url, "bron_term": bron_term, "status": "nieuw",
        }

    def zet_status(self, url: str, status: str):
        if url in self.resultaten:
            self.resultaten[url]["status"] = status

    def wis_blok(self, pagina_url: str):
        """Pagina + al haar suburls op 'geskipt' (bulk-wissen van één blok)."""
        for r in self.resultaten.values():
            if r["url"] == pagina_url or r.get("parent_url") == pagina_url:
                r["status"] = "geskipt"

    def wis_run(self, run: str):
        """Alle nog-actieve resultaten van één run op 'geskipt'."""
        for r in self.resultaten.values():
            if r["run"] == run and r["status"] in ("nieuw", "bewaard"):
                r["status"] = "geskipt"

    # -- opvragen ------------------------------------------------------------
    def actieve(self) -> list[dict]:
        """Alles wat nog telt voor de GUI: nieuw of bewaard."""
        return [r for r in self.resultaten.values() if r["status"] in ("nieuw", "bewaard")]

    # -- wegschrijven --------------------------------------------------------
    def bewaar(self):
        data = {
            "profiel": self.naam,
            "bijgewerkt": datetime.now().isoformat(timespec="seconds"),
            "gezien_urls": sorted(self.gezien),
            "resultaten": list(self.resultaten.values()),
        }
        _schrijf_veilig(self.pad, json.dumps(data, ensure_ascii=False, indent=2))
        self._schrijf_export()

    def _schrijf_export(self):
        """De schone oogst: alleen bewaarde, nog niet bezochte urls (klikbaar)."""
        oogst = [
            {"url": r["url"], "titel": r["titel"], "type": r["type"],
             "samenvatting": r["samenvatting"], "oordeel": r["oordeel"]}
            for r in self.resultaten.values() if r["status"] == "bewaard"
        ]
        export = {"profiel": self.naam,
                  "bijgewerkt": datetime.now().isoformat(timespec="seconds"),
                  "aantal": len(oogst), "urls": oogst}
        _schrijf_veilig(self.export_pad, json.dumps(export, ensure_ascii=False, indent=2))


# ----------------------------------------------------------------------------- veilig schrijven
def _schrijf_veilig(pad: Path, tekst: str):
    """Schrijf zonder risico op dataverlies: eerst naar een tijdelijk bestand, dan
    de vorige goede versie als .bak opzijzetten en het tijdelijke bestand op zijn
    plaats schuiven. Een crash midden in het schrijven laat zo nooit een half of
    leeg hoofdbestand achter; de vorige versie blijft als .bak bewaard."""
    tijdelijk = pad.with_suffix(pad.suffix + ".tmp")
    tijdelijk.write_text(tekst, encoding="utf-8")
    if pad.exists():
        try:
            pad.replace(pad.with_suffix(pad.suffix + ".bak"))
        except OSError:
            pass                                  # back-up mislukt: schrijven gaat door
    tijdelijk.replace(pad)
