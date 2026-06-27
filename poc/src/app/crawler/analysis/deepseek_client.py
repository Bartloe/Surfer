# src/app/crawler/analysis/deepseek_client.py
import httpx
from typing import Dict

class DeepSeekClient:
    """
    Wrapper voor DeepSeek Chat Completion API.
    Verwacht:
    - title
    - text
    - description
    - metadata
    Geeft terug:
    - summary (300 woorden)
    - match_score (1-10)
    - relevance_score (1-10)
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    async def analyze(self, title: str, text: str, description: str, metadata: Dict) -> Dict:
        prompt = self._build_prompt(title, text, description, metadata)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        body = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert TV series analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.base_url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return self._parse_response(content)

    # ---------------------------------------------------------
    # PROMPT GENERATIE
    # ---------------------------------------------------------
    def _build_prompt(self, title: str, text: str, description: str, metadata: Dict) -> str:
        # Beperk tekst tot 8000 tekens (DeepSeek context)
        truncated_text = text[:8000]
        return f"""
Analyseer de volgende webpagina en bepaal of deze relevant is voor het vinden van **nieuwe TV-series** (uitgezonden in 2026 of later, of nog niet uitgezonden).

**Belangrijke criteria:**
- Alleen series die **in 2026 of later** zijn verschenen of nog gaan verschijnen.
- Geen boeken, films, trailers, reality-tv, anime, of bestaande series van vóór 2026.
- Geef een score (1-10) voor hoe goed de pagina past bij de zoekopdracht.

Titel: {title}

Beschrijving: {description}

Tekst (eerste 8000 tekens):
{truncated_text}

Metadata:
{metadata}

Geef een JSON-response met exact deze structuur:
{{
  "summary": "Een korte samenvatting van de meest relevante nieuwe serie op deze pagina (max 300 woorden).",
  "match_score": <score 1-10, hoger = relevanter>,
  "relevance_score": <score 1-10, gebaseerd op hoe goed de serie past bij de zoekterm>
}}

Let op: als de pagina meerdere series noemt, kies dan de serie die het beste past bij de zoekterm en die aan het 'nieuw'-criterium voldoet.
"""

    # ---------------------------------------------------------
    # JSON PARSER
    # ---------------------------------------------------------
    def _parse_response(self, content: str) -> Dict:
        import json

        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
            return json.loads(json_str)
        except Exception:
            return {
                "summary": content,
                "match_score": 0,
                "relevance_score": 0
            }