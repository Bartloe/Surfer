"""
rapport_zoektermen — los rapport van de zoekterm-analyse (scherm + tekstbestand).

Versie: 1.0
Reden:  Nieuw — draait de zoekterm-analyse buiten de app om en zet een nette tabel op
        het scherm én in resultaten/<profiel>_zoektermen.txt. De tabel-opmaak
        ('formatteer') wordt ook door de GUI-knop hergebruikt, zodat beide hetzelfde
        tonen.
Datum:  2026-06-30 23:25 (NL)

Draaien:  .venv/Scripts/python.exe rapport_zoektermen.py <profiel>
          (zonder profiel: toont de beschikbare profielnamen)
"""

import sys

import analyse
import opslag as opslag_mod

KOLOMMEN = [
    ("zoekterm", "Zoekterm", 42, "links"),
    ("bewaard", "Bewaard", 8, "rechts"),
    ("weggegooid", "Weg", 6, "rechts"),
    ("nieuw", "Nieuw", 7, "rechts"),
    ("trefkans", "Trefkans", 9, "rechts"),
    ("gem_cijfer", "Gem.cijfer", 11, "rechts"),
]


def _cel(rij: dict, sleutel: str) -> str:
    waarde = rij.get(sleutel)
    if sleutel == "trefkans":
        return "—" if waarde is None else f"{waarde * 100:.0f}%"
    if sleutel == "gem_cijfer":
        return "—" if waarde is None else f"{waarde:.1f}"
    return str(waarde)


def formatteer(rijen: list[dict]) -> str:
    """Maak een uitgelijnde tekst-tabel van de analyse-rijen (ook door de GUI gebruikt)."""
    if not rijen:
        return "Nog geen vondsten om te analyseren — draai eerst een zoekronde."

    def regel(cellen: list[str]) -> str:
        delen = []
        for (_, _, breedte, kant), tekst in zip(KOLOMMEN, cellen):
            tekst = tekst[:breedte]
            delen.append(tekst.ljust(breedte) if kant == "links" else tekst.rjust(breedte))
        return "  ".join(delen)

    kop = regel([k[1] for k in KOLOMMEN])
    streep = "-" * len(kop)
    body = [regel([_cel(r, k[0]) for k in KOLOMMEN]) for r in rijen]

    totaal_bewaard = sum(r["bewaard"] for r in rijen)
    totaal_weg = sum(r["weggegooid"] for r in rijen)
    voet = (f"\nTotaal: {len(rijen)} zoekterm(en), "
            f"{totaal_bewaard} bewaard, {totaal_weg} weggegooid.\n"
            "Beste bovenaan (meeste bewaard); lage trefkans = veel ruis.")
    return "\n".join([kop, streep, *body]) + "\n" + voet


def schrijf_rapport(naam: str) -> str:
    """Analyseer een profiel, toon de tabel en bewaar 'm als tekstbestand."""
    rijen = analyse.analyseer_profiel(naam)
    tekst = f"Zoekterm-analyse — profiel '{naam}'\n\n" + formatteer(rijen)
    opslag_mod.RESULTATEN_MAP.mkdir(exist_ok=True)
    pad = opslag_mod.RESULTATEN_MAP / f"{naam}_zoektermen.txt"
    try:
        pad.write_text(tekst, encoding="utf-8")
    except OSError as e:
        tekst += f"\n\n(Let op: kon het rapportbestand niet schrijven: {e})"
    else:
        tekst += f"\n\nOok bewaard als: {pad.name}"
    return tekst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        namen = opslag_mod.lijst_profielen()
        print("Gebruik: rapport_zoektermen.py <profiel>")
        print("Beschikbare profielen:", ", ".join(namen) if namen else "(geen)")
        sys.exit(1)
    print(schrijf_rapport(sys.argv[1]))
