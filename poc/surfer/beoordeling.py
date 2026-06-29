"""
beoordeling — goedkope, ruime voor-schifting via DeepSeek.

Versie: 1.1
Reden:  Uitsluitingen uit de config worden nu écht gebruikt: een ZACHTE uitsluit-hint
        in de prompt (alleen wegfilteren bij een duidelijke match; bij twijfel insluiten,
        zodat de recall behouden blijft en een afnemer de fijne controle kan doen).
Datum:  2026-06-29 (NL)

Versie: 1.0
Reden:  Fase 0 — prompt herschreven: recall + grove smaak + meerdere vondsten
        per pagina (listicles). Géén harde smaak-poort.
Datum:  2026-06-27 17:56 (NL)

- Beoordelaar is een protocol; de pipeline hangt hieraan, niet aan DeepSeek
  rechtstreeks. Zo is hij testbaar (nep-beoordelaar) en vervangbaar.
- DeepSeekBeoordelaar stelt twee vragen tegelijk, ruim/recall-gericht:
    1) is dit een echte, NIEUWE serie met genoeg info?  (relevantie)
    2) past dit GROFWEG bij het meegegeven profiel?      (grove smaak, 0-10)
  De grove smaak rangschikt alleen; hij filtert NOOIT weg.
- Eén pagina mag MEERDERE vondsten opleveren (een "10 beste"-lijst telt mee).
- profiel_tekst + uitsluitingen komen van buitenaf binnen; staan niet in deze module.
- uitsluitingen = neutrale gewone-taal-zinnen ("geen X-series"); een ZACHTE hint, geen
  harde poort. Bij twijfel insluiten — wat hier wegvalt, ziet de afnemer nooit meer.
"""

import json
from typing import Protocol

import httpx


class Beoordelaar(Protocol):
    def beoordeel(self, titel: str, tekst: str, profiel_tekst: str,
                  uitsluitingen: list[str] | None = None) -> list[dict]:
        ...


class DeepSeekBeoordelaar:
    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com/v1/chat/completions",
                 timeout: int = 40):
        if not api_key:
            raise ValueError("DeepSeek-sleutel ontbreekt (zet DEEPSEEK_API_KEY in .env).")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def beoordeel(self, titel: str, tekst: str, profiel_tekst: str,
                  uitsluitingen: list[str] | None = None) -> list[dict]:
        prompt = self._bouw_prompt(titel, tekst, profiel_tekst, uitsluitingen)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Je bent een nuchtere ontdek-assistent voor nieuwe tv-series."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        with httpx.Client(timeout=self.timeout) as client:
            antwoord = client.post(self.base_url, headers=headers, json=body)
            antwoord.raise_for_status()
            data = antwoord.json()
        inhoud = data["choices"][0]["message"]["content"]
        return self._lees_vondsten(inhoud)

    def _bouw_prompt(self, titel: str, tekst: str, profiel_tekst: str,
                     uitsluitingen: list[str] | None = None) -> str:
        tekst = (tekst or "")[:8000]
        profiel_blok = profiel_tekst.strip() or "(geen profiel meegegeven — beoordeel alleen op relevantie)"
        schoon = [u.strip() for u in (uitsluitingen or []) if u and u.strip()]
        if schoon:
            regels = "\n".join(f"- {u}" for u in schoon)
            uitsluit_blok = (
                "\nLaat een serie alléén weg als die DUIDELIJK onder een van deze "
                "uitsluitingen valt. Bij twijfel: tóch meenemen (een latere stap doet de "
                "fijne controle). Sluit nooit uit op smaak — dit zijn harde categorieën:\n"
                f"{regels}\n")
        else:
            uitsluit_blok = ""
        return f"""
Bekijk deze webpagina en haal ALLE echte, NIEUWE tv-series eruit (uitgezonden in
2026 of later, of nog te verschijnen). Eén pagina kan meerdere series noemen
(bijv. een "10 beste nieuwe series"-lijst): geef ze dan ALLEMAAL terug, niet één.

Negeer: boeken, films, trailers-zonder-serie, losse afleveringen, en bestaande
series van vóór 2026.

Voor elke serie geef je twee losse oordelen:
- relevantie: is dit een echte, nieuwe serie met genoeg informatie? (waarom kort)
- grove smaak: past dit GLOBAAL bij onderstaand profiel? Geef 0-10. Dit is alleen
  een grove rangschikking; sluit NIETS uit op smaak — bij twijfel ruim insluiten.

Profiel (smaakvoorkeur van de afnemer):
{profiel_blok}
{uitsluit_blok}
Paginatitel: {titel}

Paginatekst (eerste 8000 tekens):
{tekst}

Antwoord UITSLUITEND met JSON in exact deze vorm:
{{
  "vondsten": [
    {{
      "titel": "<serietitel>",
      "samenvatting": "<korte omschrijving van de serie, max 120 woorden>",
      "taal": "<vermoedelijke taal, ISO zoals nl/en/fr; leeg indien onbekend>",
      "is_relevant": true,
      "relevantie_reden": "<waarom dit een echte, nieuwe serie is>",
      "smaak_indicatie": <getal 0-10>
    }}
  ]
}}
Als de pagina geen enkele nieuwe serie bevat: geef {{"vondsten": []}}.
"""

    def _lees_vondsten(self, inhoud: str) -> list[dict]:
        try:
            start = inhoud.index("{")
            einde = inhoud.rindex("}") + 1
            data = json.loads(inhoud[start:einde])
            vondsten = data.get("vondsten", [])
            return vondsten if isinstance(vondsten, list) else []
        except Exception:
            return []
