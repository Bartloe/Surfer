"""
zelftest — offline controle van de keten zonder web of DeepSeek (geen kosten).

Versie: 1.2
Reden:  Test voor de nieuwe zoekterm-analyse toegevoegd (telling per zoekterm,
        trefkans, gemiddeld cijfer, sortering, en '(onbekend)' voor herkomstloze
        vondsten). Eerder (v1.1): test draait in een wegwerpmap, raakt nooit echte data.
Datum:  2026-06-30 23:30 (NL)

Draaien:  .venv/Scripts/python.exe zelftest.py
Faalt luid (assert) zodra er iets stuk is; print 'ALLES GROEN' als alles klopt.
"""

import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import analyse
import graafwerk
import kern
import opslag as opslag_mod


@contextmanager
def tijdelijke_opslag():
    """Verleg profielen/resultaten naar een wegwerpmap, zodat de zelftest NOOIT
    echte vondsten aanraakt of wist. Zet alles na afloop weer terug."""
    map = Path(tempfile.mkdtemp(prefix="surfer_zelftest_"))
    orig_prof, orig_res = opslag_mod.PROFIELEN_MAP, opslag_mod.RESULTATEN_MAP
    opslag_mod.PROFIELEN_MAP = map / "profielen"
    opslag_mod.RESULTATEN_MAP = map / "resultaten"
    opslag_mod.PROFIELEN_MAP.mkdir(parents=True)
    opslag_mod.RESULTATEN_MAP.mkdir(parents=True)
    try:
        yield
    finally:
        opslag_mod.PROFIELEN_MAP, opslag_mod.RESULTATEN_MAP = orig_prof, orig_res
        shutil.rmtree(map, ignore_errors=True)


def test_profiel_lezen():
    with tijdelijke_opslag():
        opslag_mod.profiel_pad("testprofiel").write_text(
            "Zoektermen:\nwedstrijd\ngoal\n\nContext:\nvideo's over voetbal\n",
            encoding="utf-8")
        zoektermen, context = opslag_mod.lees_profiel("testprofiel")
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
    import json
    with tijdelijke_opslag():
        opslag_mod.profiel_pad("testprofiel").write_text(
            "Zoektermen:\nwedstrijd\ngoal\n\nContext:\nvideo's over voetbal\n",
            encoding="utf-8")

        # graafwerk tijdelijk vervangen door de nep-versie
        nep = NepGraafwerk()
        origineel = (graafwerk.zoek_videos, graafwerk.zoek_paginas,
                     graafwerk.haal_pagina, graafwerk.videos_op_pagina)
        kern.graafwerk.zoek_videos = nep.zoek_videos
        kern.graafwerk.zoek_paginas = nep.zoek_paginas
        kern.graafwerk.haal_pagina = nep.haal_pagina
        kern.graafwerk.videos_op_pagina = nep.videos_op_pagina
        try:
            res = kern.run("testprofiel", drempel=6.0, oordelaar=NepOordeel(), log=lambda *a: None)
        finally:
            (kern.graafwerk.zoek_videos, kern.graafwerk.zoek_paginas,
             kern.graafwerk.haal_pagina, kern.graafwerk.videos_op_pagina) = origineel
        assert res["nieuw"] > 0, "run leverde niets op"

        winkel = opslag_mod.ProfielOpslag("testprofiel")
        actief = winkel.actieve()
        assert actief, "geen actieve resultaten bewaard"
        types = {r["type"] for r in actief}
        assert "pagina" in types and "suburl" in types, "pagina/suburl ontbreekt"

        # statussen: bewaren -> in export; bezoeken -> eruit
        pagina = next(r for r in actief if r["type"] == "pagina")
        winkel.zet_status(pagina["url"], "bewaard")
        winkel.bewaar()
        export = json.loads(winkel.export_pad.read_text(encoding="utf-8"))
        assert export["aantal"] == 1, "bewaarde url niet in export"
        winkel.zet_status(pagina["url"], "bezocht")
        winkel.bewaar()
        export = json.loads(winkel.export_pad.read_text(encoding="utf-8"))
        assert export["aantal"] == 0, "bezochte url valt niet uit export"

        # veilig schrijven: na een tweede bewaar bestaat er een .bak-reservekopie
        assert winkel.pad.with_suffix(winkel.pad.suffix + ".bak").exists(), \
            "geen .bak-reservekopie gemaakt"

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
            res2 = kern.run("testprofiel", drempel=6.0, oordelaar=NepOordeel(), log=lambda *a: None)
        finally:
            (kern.graafwerk.zoek_videos, kern.graafwerk.zoek_paginas,
             kern.graafwerk.haal_pagina, kern.graafwerk.videos_op_pagina) = origineel
        assert res2["nieuw"] == 0, "geheugen werkt niet — zelfde urls opnieuw toegevoegd"
    print("  run + statussen + export + geheugen + bulk-wis + .bak — ok")


def test_zoekterm_analyse():
    # Drie zoektermen met uiteenlopende oogst; een record zonder bron_term -> '(onbekend)'.
    resultaten = [
        {"bron_term": "goal", "status": "bewaard", "oordeel": "top", "score": 9.0},
        {"bron_term": "goal", "status": "bewaard", "oordeel": "top", "score": 7.0},
        {"bron_term": "goal", "status": "geskipt", "oordeel": "matig", "score": 5.0},
        {"bron_term": "ruis", "status": "geskipt", "oordeel": "nee", "score": 4.0},
        {"bron_term": "ruis", "status": "bewaard", "oordeel": "ok", "score": 6.0},
        {"bron_term": "open", "status": "nieuw", "oordeel": "", "score": 8.0},
        {"status": "bewaard", "oordeel": "los", "score": 8.0},   # geen bron_term
    ]
    rijen = analyse.analyseer(resultaten)
    per_term = {r["zoekterm"]: r for r in rijen}

    assert per_term["goal"]["bewaard"] == 2 and per_term["goal"]["weggegooid"] == 1
    assert abs(per_term["goal"]["trefkans"] - 2 / 3) < 1e-9, "trefkans goal klopt niet"
    assert abs(per_term["goal"]["gem_cijfer"] - 7.0) < 1e-9, "gem. cijfer goal klopt niet"
    assert per_term["open"]["nieuw"] == 1 and per_term["open"]["trefkans"] is None
    assert analyse.ONBEKEND in per_term, "record zonder bron_term niet onder (onbekend)"
    # sortering: meeste bewaard eerst -> 'goal' (2) staat vóór 'ruis' (1)
    volgorde = [r["zoekterm"] for r in rijen]
    assert volgorde.index("goal") < volgorde.index("ruis"), "sortering op bewaard klopt niet"
    print(f"  zoekterm-analyse: {len(rijen)} termen, sortering + trefkans + cijfer — ok")


if __name__ == "__main__":
    print("Zelftest stand-alone Surfer:")
    test_profiel_lezen()
    test_videos_op_pagina()
    test_run_en_statussen()
    test_zoekterm_analyse()
    print("ALLES GROEN")
    sys.exit(0)
