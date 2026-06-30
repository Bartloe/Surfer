"""
oordeel — generiek DeepSeek-oordeel: sluit de inhoud aan bij het profiel?

Versie: 1.0
Reden:  Eerste versie — onderwerp-onafhankelijk oordeel (geen tv-series-aanname).
Datum:  2026-06-30 19:18 (NL)

- DeepSeekOordeel beoordeelt één treffer (pagina of video) tegen de profiel-context.
- Geeft terug: past (ja/nee), score 0-10, korte samenvatting, integraal oordeel.
- De sleutel komt uit .env (DEEPSEEK_API_KEY); ontbreekt die, dan een heldere fout.
- Beoordelaar is inwisselbaar (zelfde vorm), zodat de zelftest een nep-oordeel
  kan injecteren zonder kosten.
"""

import json

import httpx


class DeepSeekOordeel:
    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com/v1/chat/completions",
                 timeout: int = 40):
        if not api_key:
            raise ValueError("DeepSeek-sleutel ontbreekt (zet DEEPSEEK_API_KEY in .env).")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def beoordeel(self, titel: str, tekst: str, context: str) -> dict:
        prompt = self._bouw_prompt(titel, tekst, context)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system",
                 "content": "Je beoordeelt nuchter of gevonden webinhoud aansluit bij "
                            "het onderwerp en de wensen van de gebruiker."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                antwoord = client.post(self.base_url, headers=headers, json=body)
                antwoord.raise_for_status()
                inhoud = antwoord.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return {"past": False, "score": 0.0, "samenvatting": "",
                    "oordeel": f"(geen oordeel — fout bij DeepSeek: {e})"}
        return self._lees(inhoud)

    def _bouw_prompt(self, titel: str, tekst: str, context: str) -> str:
        tekst = (tekst or "")[:8000]
        context = (context or "").strip() or "(geen context meegegeven — beoordeel op relevantie)"
        return f"""
Hieronder staat het PROFIEL van een gebruiker (het onderwerp dat hij zoekt en
waar hij interessante video's / inhoud over wil vinden), gevolgd door een GEVONDEN
stuk webinhoud (een pagina of een video).

Beoordeel hoe goed de gevonden inhoud aansluit bij het profiel.

PROFIEL / CONTEXT:
{context}

GEVONDEN INHOUD
titel: {titel}
tekst (eerste 8000 tekens):
{tekst}

Antwoord UITSLUITEND met JSON in exact deze vorm:
{{
  "past": <true of false — sluit dit duidelijk aan bij het profiel?>,
  "score": <getal 0-10, hoe goed de aansluiting is>,
  "samenvatting": "<korte, feitelijke samenvatting van de inhoud, max 80 woorden>",
  "oordeel": "<jouw integrale oordeel in gewone taal: waaróm dit wel/niet aansluit>"
}}
"""

    def _lees(self, inhoud: str) -> dict:
        try:
            start = inhoud.index("{")
            einde = inhoud.rindex("}") + 1
            data = json.loads(inhoud[start:einde])
            return {
                "past": bool(data.get("past", False)),
                "score": float(data.get("score", 0) or 0),
                "samenvatting": str(data.get("samenvatting", "")).strip(),
                "oordeel": str(data.get("oordeel", "")).strip(),
            }
        except Exception:
            return {"past": False, "score": 0.0, "samenvatting": "",
                    "oordeel": "(geen oordeel — antwoord niet te lezen)"}
