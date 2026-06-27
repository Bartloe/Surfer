"""
surfer — een schone, losweekbare ontdek-feeder.

Versie: 1.0
Reden:  Fase 0 — Surfer opgeschoond tot een zelfstandige feeder.
Datum:  2026-06-27 17:56 (NL)

KERNREGEL (bewaakt de losweekbaarheid):
  Uitvoer is het contract; de afnemer is onbekend en niet onze zaak.
  Deze module kent geen enkele afnemer. Alles wat hij nodig heeft
  (smaakprofiel, zoektermen, uitsluitingen, opslaglocatie) komt als
  gewoon functie-argument binnen — nooit uit een afnemer-bestand.

Publieke ingang voor een afnemer:
  - SurferConfig : alle invoer, van buitenaf aan te reiken.
  - Vondst       : één gevonden, relevant ding (generiek).
  - Opslag       : de eigen, privé opslag van Surfer.
  - surf()       : draait één run en geeft een samenvatting terug.
"""

from .config import SurferConfig, standaard_config
from .vondst import Vondst
from .opslag import Opslag
from .pipeline import surf

__all__ = ["SurferConfig", "standaard_config", "Vondst", "Opslag", "surf"]
