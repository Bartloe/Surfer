import json
from datetime import datetime
from typing import Dict, Any

from .storage import get_relevant_results, get_failed_scrapes, get_technical_errors


def build_export_payload() -> Dict[str, Any]:
    relevant = get_relevant_results()
    failed = get_failed_scrapes()
    technical = get_technical_errors()

    return {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
        },
        "relevante_resultaten": [
            {
                "url": r.url,
                "titel": r.title,
                "samenvatting": r.summary,
                "match_score": r.match_score,
                "relevance_score": r.relevance_score,
                "zoekterm": r.search_term,
                "zoekmachine": r.engine,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in relevant
        ],
        "scrape_mislukt": [
            {
                "url": f.url,
                "label": f.label,
                "zoekterm": f.search_term,
                "zoekmachine": f.engine,
                "timestamp": f.timestamp.isoformat(),
            }
            for f in failed
        ],
        "technische_analyse": [
            {
                "url": t.url,
                "categorie": t.category,
                "omschrijving": t.description,
                "zoekterm": t.search_term,
                "zoekmachine": t.engine,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in technical
        ],
        "deepseek_begeleidende_tekst": (
            "Beste DeepSeek,\n\n"
            "Analyseer deze dataset en geef aanbevelingen voor:\n"
            "- verbetering van zoekvragen\n"
            "- verbetering van scraping-technieken\n"
            "- detectie en omzeiling van anti-bot-mechanismen\n"
            "- optimalisatie van heuristiek en snippet-filters\n"
            "- patronen in mislukte scrapes (timeout / anti-bot)\n"
            "- patronen in technische fouten (http, ssl, dns, encoding, redirects, javascript, captcha)\n\n"
            "Geef concrete aanbevelingen, prioriteiten en mogelijke oplossingsrichtingen."
        ),
    }


def build_export_file_bytes() -> bytes:
    payload = build_export_payload()
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
