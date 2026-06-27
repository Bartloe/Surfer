"""
vondst — het generieke "gevonden ding" dat Surfer aflevert.

Versie: 1.0
Reden:  Fase 0 — één heldere uitvoervorm i.p.v. losse db-rijen.
Datum:  2026-06-27 17:56 (NL)

- Beschrijft generiek een vondst (titel, bron, samenvatting, signalen).
- Bewust niet afnemer-specifiek benoemd, zodat hij herbruikbaar blijft.
- relevantie_reden = waaróm dit een echte, nieuwe vondst is (geen smaakoordeel).
- smaak_indicatie  = grove, goedkope voor-schifting (0-10); NOOIT beslissend.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class Vondst:
    titel: str
    bron_url: str
    samenvatting: str = ""
    taal: str = ""
    relevantie_reden: str = ""
    is_relevant: bool = True
    smaak_indicatie: float = 0.0
    externe_ids: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)
