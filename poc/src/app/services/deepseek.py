# Hier kun je later echte DeepSeek-API-calls neerzetten.
# Voor nu alleen de perfecte prompt als helper.

def get_deepseek_prompt() -> str:
    return """
Analyseer de meegeleverde dataset en geef je volledige antwoord uitsluitend terug in geldig JSON-formaat volgens onderstaand schema. Gebruik geen tekst buiten het JSON-object.

JSON-schema:
{
  "zoekterm_aanbevelingen": [
    "concrete verbeteringen voor zoektermen",
    "nieuwe zoektermen die kansrijk zijn",
    "zoektermen die verwijderd of aangepast moeten worden"
  ],
  "scraping_aanbevelingen": [
    "adviezen om scraping betrouwbaarder te maken",
    "patronen in timeouts en anti-bot detectie",
    "suggesties voor headless strategieën"
  ],
  "anti_bot_patronen": [
    "herkende patronen in anti-bot blokkades",
    "aanbevolen mitigaties"
  ],
  "technische_fouten_analyse": [
    "patronen in http/ssl/dns/redirect/encoding fouten",
    "concrete oplossingen per foutcategorie"
  ],
  "prioriteiten_top_5": [
    "de vijf belangrijkste acties die ik NU moet uitvoeren"
  ],
  "samenvatting_kort": "maximaal 5 zinnen met de kern van je analyse"
}

Regels:
- Gebruik uitsluitend geldig JSON.
- Geen markdown, geen uitleg buiten JSON.
- Houd alle tekst kort, concreet en actiegericht.
- Schrijf in Nederlands.
- Baseer je analyse op alle drie secties van de dataset:
  - relevante resultaten
  - scrape mislukt (timeout / anti-bot)
  - technische fouten
- Geef alleen informatie die direct helpt om de crawler te verbeteren.
""".strip()
