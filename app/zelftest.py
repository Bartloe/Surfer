"""
zelftest — offline controle van de keten zonder web of DeepSeek (geen kosten).

Versie: 1.0
Reden:  Eerste versie — bewijst graafwerk-koppeling, oordeel-flow, statussen, export.
Datum:  2026-06-30 19:18 (NL)

Draaien:  .venv/Scripts/python.exe zelftest.py
Faalt luid (assert) zodra er iets stuk is; print 'ALLES GROEN' als alles klopt.
"""

import sys

import graafwerk
import kern
import opslag as opslag_mod


def test_profiel_lezen():
    zoektermen, context = opslag_mod.lees_profiel("wk_voetbal")
    assert len(zoektermen) >= 2, "zoektermen niet gelezen"
    assert "video" in context.lower(), "context niet gelezen"
    print(f"  profiel: {len(zoektermen)} zoektermen, context {len(context)} tekens — ok")


def test_videos_op_pagina():
    html = """
    <html><body>
      <iframe src="https://www.youtube.com/embed/ABCDEF12345"></iframe>
      <a href="https://youtu.be/ZYXWVU98765">Mooie goal</a>
      <a href="https://vimeo.com/123456789">Analyse</a>
      <a href="https://example.com/artikel">geen video</a>
    </body></html>
    """
    videos = graafwerk.videos_op_pagina(html, "https://bron.nl/p")
    urls = {v.url for v in videos}
    assert "https://www.youtube.com/watch?v=ABCDEF12345" in urls, "embed niet genormaliseerd"
    assert "https://www.youtube.com/watch?v=ZYXWVU98765" in urls, "youtu.be niet gevonden"
    assert any("vimeo.com/123456789" in u for u in urls), "vimeo niet gevonden"
    assert not any("example.com/artikel" in u for u in urls), "niet-video toch meegenomen"
    print(f"  videos_op_pagina: {len(videos)} video's uit 1 pagina — ok")


class NepGraafwerk:
    """Vervangt de web-laag tijdens de test (geen internet)."""
    def zoek_videos(self, term, n):
        return [graafwerk.Treffer(url=f"https://youtu.be/vid_{term[:3]}",
                                  titel=f"video over {term}", fragment="clip", is_video=True)]
    def zoek_paginas(self, term, n):
        return [graafwerk.Treffer(url=f"https://bron.nl/{term[:3]}",
                                  titel=f"pagina over {term}", fragment="", is_video=False)]
    def haal_pagina(self, url):
        return {"html": '<a href="https://youtu.be/SUB12345678">sub</a>',
                "titel": "Bronpagina", "tekst": "Veel tekst over het onderwerp.", "fout": None}
    def videos_op_pagina(self, html, url):
        return [graafwerk.Treffer(url="https://www.youtube.com/watch?v=SUB12345678",
                                  titel="subvideo", is_video=True)]


class NepOordeel:
    def beoordeel(self, titel, tekst, context):
        return {"past": True, "score": 9.0,
                "samenvatting": f"samenvatting van {titel}",
                "oordeel": "sluit goed aan bij het profiel"}


def test_run_en_statussen():
    # graafwerk tijdelijk vervangen door de nep-versie
    nep = NepGraafwerk()
    origineel = (graafwerk.zoek_videos, graafwerk.zoek_paginas,
                 graafwerk.haal_pagina, graafwerk.videos_op_pagina)
    kern.graafwerk.zoek_videos = nep.zoek_videos
    kern.graafwerk.zoek_paginas = nep.zoek_paginas
    kern.graafwerk.haal_pagina = nep.haal_pagina
    kern.graafwerk.videos_op_pagina = nep.videos_op_pagina
    try:
        res = kern.run("wk_voetbal", drempel=6.0, oordelaar=NepOordeel(), log=lambda *a: None)
    finally:
        (kern.graafwerk.zoek_videos, kern.graafwerk.zoek_paginas,
         kern.graafwerk.haal_pagina, kern.graafwerk.videos_op_pagina) = origineel
    assert res["nieuw"] > 0, "run leverde niets op"

    winkel = opslag_mod.ProfielOpslag("wk_voetbal")
    actief = winkel.actieve()
    assert actief, "geen actieve resultaten bewaard"
    types = {r["type"] for r in actief}
    assert "pagina" in types and "suburl" in types, "pagina/suburl ontbreekt"

    # statussen: bewaren -> in export; bezoeken -> eruit
    pagina = next(r for r in actief if r["type"] == "pagina")
    winkel.zet_status(pagina["url"], "bewaard")
    winkel.bewaar()
    import json
    export = json.loads(winkel.export_pad.read_text(encoding="utf-8"))
    assert export["aantal"] == 1, "bewaarde url niet in export"
    winkel.zet_status(pagina["url"], "bezocht")
    winkel.bewaar()
    export = json.loads(winkel.export_pad.read_text(encoding="utf-8"))
    assert export["aantal"] == 0, "bezochte url valt niet uit export"

    # bulk-wissen van een blok (pagina + suburls)
    winkel.wis_blok(pagina["url"])
    assert all(r["status"] == "geskipt"
               for r in winkel.resultaten.values()
               if r["url"] == pagina["url"] or r.get("parent_url") == pagina["url"]), \
        "wis_blok werkt niet"

    # geheugen: tweede run mag niets nieuws meer toevoegen (alles al gezien)
    kern.graafwerk.zoek_videos = nep.zoek_videos
    kern.graafwerk.zoek_paginas = nep.zoek_paginas
    kern.graafwerk.haal_pagina = nep.haal_pagina
    kern.graafwerk.videos_op_pagina = nep.videos_op_pagina
    try:
        res2 = kern.run("wk_voetbal", drempel=6.0, oordelaar=NepOordeel(), log=lambda *a: None)
    finally:
        (kern.graafwerk.zoek_videos, kern.graafwerk.zoek_paginas,
         kern.graafwerk.haal_pagina, kern.graafwerk.videos_op_pagina) = origineel
    assert res2["nieuw"] == 0, "geheugen werkt niet — zelfde urls opnieuw toegevoegd"
    print("  run + statussen + export + geheugen + bulk-wis — ok")

    # opruimen: testbestanden weg
    winkel.pad.unlink(missing_ok=True)
    winkel.export_pad.unlink(missing_ok=True)


if __name__ == "__main__":
    print("Zelftest stand-alone Surfer:")
    test_profiel_lezen()
    test_videos_op_pagina()
    test_run_en_statussen()
    print("ALLES GROEN")
    sys.exit(0)
