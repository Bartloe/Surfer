"""
gui — het scherm van de stand-alone Surfer-app (customtkinter).

Versie: 1.2
Reden:  Overzicht bij veel vondsten — sorteren (hoogste score / laatste run),
        batch-weergave (N per keer) met 'wis getoonde → volgende', en bewaarde
        vondsten apart bovenaan. (1.1 = live verloop, kopieer, klik-opent-alleen.)
Datum:  2026-06-30 20:59 (NL)

- Bovenin: profiel kiezen/bewerken/nieuw, drempel + aantal, en de zoekknop.
- Live venster onder de knoppen: toont tijdens een run welke stap loopt.
- Resultaten per blok: een pagina met daaronder de video's die erop staan (suburls);
  losse video-treffers staan op zichzelf.
- Per regel: aankruisvak (bewaren), klikbare url (opent ALLEEN de browser), een
  kopieer-knop (url naar klembord), het DeepSeek-oordeel rechts, samenvatting links.
- Bulk: 'wis hele pagina' (pagina + video's erop) en 'wis alles van laatste run'.
- Draaien:  .venv/Scripts/python.exe gui.py
"""

import threading
import webbrowser

import customtkinter as ctk

import kern
import opslag as opslag_mod

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

KLEUR_LINK = "#4ea1ff"
KLEUR_WIS = "#7a2e2e"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Surfer — video's zoeken per onderwerp")
        self.geometry("1040x740")
        self.winkel: opslag_mod.ProfielOpslag | None = None
        self.laatste_run: str | None = None
        self._stop = False
        self._bezig = False

        self.sorteer = "score"            # "score" (hoogste eerst) of "run" (laatste run eerst)
        self.batch_offset = 0             # bij welke eenheid het zichtbare blok begint
        self._batch_historie: list[int] = []
        self._volgende_offset = 0         # waar 'Volgende' heen springt (gezet in _teken)
        self._huidige_batch_units: list[dict] = []

        self._bouw_bovenbalk()
        self._bouw_resultaten()
        self._bouw_batchbalk()
        self._bouw_log()
        self._bouw_onderbalk()
        self._herlaad_profielen()

    # ------------------------------------------------------------------ opbouw
    def _bouw_bovenbalk(self):
        balk = ctk.CTkFrame(self)
        balk.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(balk, text="Profiel:").pack(side="left", padx=(8, 4))
        self.profiel_var = ctk.StringVar(value="")
        self.profiel_menu = ctk.CTkOptionMenu(balk, variable=self.profiel_var,
                                              values=[""], width=200,
                                              command=lambda _=None: self._kies_profiel())
        self.profiel_menu.pack(side="left")
        ctk.CTkButton(balk, text="Bewerken", width=80, command=self._bewerk).pack(side="left", padx=4)
        ctk.CTkButton(balk, text="Nieuw", width=70, command=self._nieuw).pack(side="left", padx=4)

        ctk.CTkLabel(balk, text="Drempel:").pack(side="left", padx=(16, 2))
        self.drempel_var = ctk.StringVar(value="6")
        ctk.CTkEntry(balk, textvariable=self.drempel_var, width=40).pack(side="left")
        ctk.CTkLabel(balk, text="Max/term:").pack(side="left", padx=(10, 2))
        self.max_var = ctk.StringVar(value="12")
        ctk.CTkEntry(balk, textvariable=self.max_var, width=40).pack(side="left")

        self.zoek_knop = ctk.CTkButton(balk, text="Zoeken", width=90, command=self._zoek)
        self.zoek_knop.pack(side="left", padx=(16, 4))
        self.stop_knop = ctk.CTkButton(balk, text="Stop", width=60, state="disabled",
                                       command=self._vraag_stop)
        self.stop_knop.pack(side="left")

    def _bouw_resultaten(self):
        self.lijst = ctk.CTkScrollableFrame(self, label_text="Resultaten")
        self.lijst.pack(fill="both", expand=True, padx=10, pady=4)

    def _bouw_batchbalk(self):
        balk = ctk.CTkFrame(self)
        balk.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(balk, text="Sorteer:").pack(side="left", padx=(8, 2))
        self.sorteer_menu = ctk.CTkOptionMenu(
            balk, values=["Hoogste score", "Laatste run"], width=150,
            command=self._zet_sorteer)
        self.sorteer_menu.set("Hoogste score")
        self.sorteer_menu.pack(side="left")

        ctk.CTkLabel(balk, text="Per batch:").pack(side="left", padx=(16, 2))
        self.batch_var = ctk.StringVar(value="25")
        ctk.CTkEntry(balk, textvariable=self.batch_var, width=44).pack(side="left")

        self.knop_vorige = ctk.CTkButton(balk, text="◀ Vorige", width=80,
                                         command=self._vorige_batch)
        self.knop_vorige.pack(side="left", padx=(16, 4))
        self.knop_volgende = ctk.CTkButton(balk, text="Volgende ▶", width=90,
                                           command=self._volgende_batch)
        self.knop_volgende.pack(side="left", padx=4)
        ctk.CTkButton(balk, text="Wis getoonde (niet-bewaard)", fg_color=KLEUR_WIS,
                      command=self._wis_batch).pack(side="left", padx=8)
        self.batch_info = ctk.CTkLabel(balk, text="", anchor="e")
        self.batch_info.pack(side="right", padx=10)

    def _bouw_log(self):
        kader = ctk.CTkFrame(self)
        kader.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(kader, text="Live verloop", anchor="w").pack(fill="x", padx=8, pady=(4, 0))
        self.log_box = ctk.CTkTextbox(kader, height=150, wrap="none",
                                      font=ctk.CTkFont(size=11))
        self.log_box.pack(fill="x", padx=8, pady=(2, 8))
        self.log_box.configure(state="disabled")

    def _log(self, tekst):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", tekst + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _bouw_onderbalk(self):
        balk = ctk.CTkFrame(self)
        balk.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkButton(balk, text="Wis alles van laatste run", fg_color=KLEUR_WIS,
                      command=self._wis_run).pack(side="left", padx=6)
        self.status_label = ctk.CTkLabel(balk, text="Klaar.", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True, padx=10)

    # ----------------------------------------------------------------- profielen
    def _herlaad_profielen(self, selecteer: str | None = None):
        namen = opslag_mod.lijst_profielen() or [""]
        self.profiel_menu.configure(values=namen)
        keuze = selecteer or (self.profiel_var.get() if self.profiel_var.get() in namen else namen[0])
        self.profiel_var.set(keuze)
        self._kies_profiel()

    def _kies_profiel(self):
        naam = self.profiel_var.get()
        self.winkel = opslag_mod.ProfielOpslag(naam) if naam else None
        self.laatste_run = None
        self._teken()

    def _bewerk(self):
        naam = self.profiel_var.get()
        if not naam:
            return
        top = ctk.CTkToplevel(self)
        top.title(f"Profiel bewerken: {naam}")
        top.geometry("640x520")
        ctk.CTkLabel(top, text="Gebruik de kopjes 'Zoektermen:' en 'Context:'.").pack(pady=(8, 0))
        box = ctk.CTkTextbox(top)
        box.pack(fill="both", expand=True, padx=8, pady=8)
        box.insert("1.0", opslag_mod.profiel_pad(naam).read_text(encoding="utf-8"))

        def opslaan():
            opslag_mod.profiel_pad(naam).write_text(box.get("1.0", "end-1c"), encoding="utf-8")
            top.destroy()

        ctk.CTkButton(top, text="Opslaan", command=opslaan).pack(pady=(0, 8))
        top.after(120, top.lift)

    def _nieuw(self):
        dlg = ctk.CTkInputDialog(text="Naam van het nieuwe profiel:", title="Nieuw profiel")
        naam = (dlg.get_input() or "").strip().replace(" ", "_")
        if not naam:
            return
        pad = opslag_mod.profiel_pad(naam)
        if not pad.exists():
            pad.write_text("Zoektermen:\n\n\nContext:\n", encoding="utf-8")
        self._herlaad_profielen(selecteer=naam)
        self._bewerk()

    # --------------------------------------------------------------------- zoeken
    def _zoek(self):
        if self._bezig or not self.profiel_var.get():
            return
        try:
            drempel = float(self.drempel_var.get().replace(",", "."))
        except ValueError:
            drempel = 6.0
        try:
            maxn = int(self.max_var.get())
        except ValueError:
            maxn = 12
        self._bezig = True
        self._stop = False
        self.zoek_knop.configure(state="disabled")
        self.stop_knop.configure(state="normal")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._status("Bezig met zoeken…")
        threading.Thread(target=self._run_thread,
                         args=(self.profiel_var.get(), drempel, maxn), daemon=True).start()

    def _run_thread(self, profiel, drempel, maxn):
        def log(m):
            self.after(0, self._log, m)

        def voortgang(i, n, term):
            self.after(0, self._status, f"Zoekterm {i}/{n}: {term}")

        try:
            oordelaar = kern.maak_oordelaar()
        except Exception as e:
            self.after(0, self._status, f"FOUT: {e}")
            self.after(0, self._na_run, profiel)
            return
        try:
            res = kern.run(profiel, drempel=drempel, max_per_term=maxn,
                           oordelaar=oordelaar, log=log, voortgang=voortgang,
                           stop=lambda: self._stop)
            self.after(0, self._status, f"Klaar — {res.get('nieuw', 0)} nieuwe treffer(s).")
            self.laatste_run = res.get("run")
        except Exception as e:
            self.after(0, self._status, f"Fout tijdens zoeken: {e}")
        self.after(0, self._na_run, profiel)

    def _na_run(self, profiel):
        self._bezig = False
        self.zoek_knop.configure(state="normal")
        self.stop_knop.configure(state="disabled")
        self.winkel = opslag_mod.ProfielOpslag(profiel)
        self._teken()

    def _vraag_stop(self):
        self._stop = True
        self._status("Stoppen na de huidige stap…")

    # ----------------------------------------------------------------- acties
    def _bewaar_toggle(self, url, var):
        if self.winkel:
            self.winkel.zet_status(url, "bewaard" if var.get() else "nieuw")
            self.winkel.bewaar()

    def _open(self, url):
        # Aanklikken = bladeren: alleen de browser openen. De url blijft staan;
        # weghalen doe je bewust met 'wis' of 'wis hele pagina'.
        webbrowser.open(url)
        self._status("Geopend in de browser (url blijft in de lijst staan).")

    def _kopieer(self, url):
        self.clipboard_clear()
        self.clipboard_append(url)
        self._status("URL naar het klembord gekopieerd.")

    def _wis_een(self, url):
        if self.winkel:
            self.winkel.zet_status(url, "geskipt")
            self.winkel.bewaar()
            self._teken()

    def _wis_blok(self, pagina_url):
        if self.winkel:
            self.winkel.wis_blok(pagina_url)
            self.winkel.bewaar()
            self._teken()

    def _wis_run(self):
        if self.winkel and self.laatste_run:
            self.winkel.wis_run(self.laatste_run)
            self.winkel.bewaar()
            self._teken()
        else:
            self._status("Geen verse run om te wissen.")

    # ----------------------------------------------------------------- tekenen
    def _status(self, tekst):
        self.status_label.configure(text=tekst)

    def _teken(self):
        for w in self.lijst.winfo_children():
            w.destroy()
        self._huidige_batch_units = []
        if not self.winkel:
            self._update_batchbalk(0, 0, 0)
            return
        actief = self.winkel.actieve()
        if not actief:
            ctk.CTkLabel(self.lijst, text="(nog geen resultaten — kies een profiel en zoek)"
                         ).pack(pady=20)
            self._update_batchbalk(0, 0, 0)
            return

        # 1) Bewaarde vondsten staan apart bovenaan (jouw keepers, altijd in beeld).
        bewaard = [r for r in actief if r["status"] == "bewaard"]
        if bewaard:
            blok = self._blok()
            ctk.CTkLabel(blok, text=f"✅ Bewaard ({len(bewaard)})", anchor="w"
                         ).pack(fill="x", padx=6, pady=(4, 2))
            for r in bewaard:
                self._subrij(blok, r)

        # 2) Nieuwe vondsten: in eenheden (pagina + video's eronder horen bij elkaar),
        #    gesorteerd, en in batches van N getoond.
        units = self._sorteer_units(self._maak_units(
            [r for r in actief if r["status"] == "nieuw"]))
        if not units:
            self._update_batchbalk(0, 0, 0)
            return

        grootte = self._batch_grootte()
        start = min(self.batch_offset, len(units) - 1)
        rijen, i = 0, start
        while i < len(units) and (rijen < grootte or not self._huidige_batch_units):
            self._render_unit(units[i])
            self._huidige_batch_units.append(units[i])
            rijen += units[i]["rijen"]
            i += 1
        self._volgende_offset = i
        self._update_batchbalk(start, i, len(units))

    # -- batch-helpers --------------------------------------------------------
    def _batch_grootte(self) -> int:
        try:
            return max(1, int(self.batch_var.get()))
        except (ValueError, AttributeError):
            return 25

    def _maak_units(self, nieuw: list[dict]) -> list[dict]:
        """Groepeer nieuwe vondsten: pagina + haar video's = één eenheid; losse
        video's en weesvideo's elk een eigen eenheid. 'rijen' telt de schermregels."""
        suburls = [r for r in nieuw if r["type"] == "suburl"]
        per_ouder: dict[str, list] = {}
        for s in suburls:
            per_ouder.setdefault(s.get("parent_url"), []).append(s)
        units: list[dict] = []
        gebruikt: set[str] = set()
        for p in [r for r in nieuw if r["type"] == "pagina"]:
            kids = per_ouder.get(p["url"], [])
            gebruikt.update(s["url"] for s in kids)
            units.append({"soort": "pagina", "hoofd": p, "subs": kids,
                          "rijen": 1 + len(kids), "score": p.get("score") or 0,
                          "run": p.get("run", "")})
        for v in [r for r in nieuw if r["type"] == "video"]:
            units.append({"soort": "video", "hoofd": v, "subs": [], "rijen": 1,
                          "score": v.get("score") or 0, "run": v.get("run", "")})
        for s in suburls:
            if s["url"] not in gebruikt:                      # ouder al weg
                units.append({"soort": "wees", "hoofd": s, "subs": [], "rijen": 1,
                              "score": s.get("score") or 0, "run": s.get("run", "")})
        return units

    def _sorteer_units(self, units: list[dict]) -> list[dict]:
        if self.sorteer == "run":
            return sorted(units, key=lambda u: (u["run"], u["score"]), reverse=True)
        return sorted(units, key=lambda u: u["score"], reverse=True)

    def _render_unit(self, u: dict):
        if u["soort"] == "pagina":
            blok = self._blok()
            self._hoofdrij(blok, u["hoofd"], wis_blok=True)
            for s in u["subs"]:
                self._subrij(blok, s)
        elif u["soort"] == "video":
            self._hoofdrij(self._blok(), u["hoofd"], wis_blok=False)
        else:
            self._subrij(self._blok(), u["hoofd"])

    def _update_batchbalk(self, start: int, eind: int, totaal: int):
        getoond = max(0, eind - start)
        self.batch_info.configure(
            text=f"Toont {start + 1}–{eind} van {totaal}" if totaal else "Niets te tonen")
        self.knop_volgende.configure(state="normal" if eind < totaal else "disabled")
        self.knop_vorige.configure(
            state="normal" if (self._batch_historie or start > 0) else "disabled")

    def _zet_sorteer(self, keuze: str):
        self.sorteer = "run" if "run" in keuze.lower() else "score"
        self.batch_offset = 0
        self._batch_historie.clear()
        self._teken()

    def _volgende_batch(self):
        if self._volgende_offset > self.batch_offset:
            self._batch_historie.append(self.batch_offset)
            self.batch_offset = self._volgende_offset
            self._teken()

    def _vorige_batch(self):
        self.batch_offset = self._batch_historie.pop() if self._batch_historie else 0
        self._teken()

    def _wis_batch(self):
        """De nu getoonde, nog niet-bewaarde vondsten weggooien en de volgende tonen."""
        if not self.winkel:
            return
        weg = 0
        for u in self._huidige_batch_units:
            for r in [u["hoofd"], *u["subs"]]:
                if r["status"] == "nieuw":
                    self.winkel.zet_status(r["url"], "geskipt")
                    weg += 1
        self.winkel.bewaar()
        self._status(f"{weg} getoonde vondst(en) weggegooid (bewaarde bleven staan).")
        self._teken()

    def _blok(self):
        blok = ctk.CTkFrame(self.lijst, border_width=1)
        blok.pack(fill="x", padx=4, pady=5)
        return blok

    def _hoofdrij(self, parent, r, wis_blok):
        kop = ctk.CTkFrame(parent, fg_color="transparent")
        kop.pack(fill="x", padx=6, pady=(6, 0))

        var = ctk.BooleanVar(value=(r["status"] == "bewaard"))
        ctk.CTkCheckBox(kop, text="bewaar", width=70, variable=var,
                        command=lambda u=r["url"], v=var: self._bewaar_toggle(u, v)
                        ).pack(side="left")
        merk = {"video": "🎬", "pagina": "📄", "suburl": "🎬"}.get(r["type"], "•")
        ctk.CTkButton(kop, text=f"{merk}  {(r['titel'] or r['url'])[:95]}", anchor="w",
                      fg_color="transparent", text_color=KLEUR_LINK, hover=False,
                      command=lambda u=r["url"]: self._open(u)
                      ).pack(side="left", fill="x", expand=True, padx=4)
        if r.get("score"):
            ctk.CTkLabel(kop, text=f"{r['score']:.0f}", width=26).pack(side="left")
        ctk.CTkButton(kop, text="kopieer", width=64,
                      command=lambda u=r["url"]: self._kopieer(u)).pack(side="left", padx=4)
        if wis_blok:
            ctk.CTkButton(kop, text="wis hele pagina", width=110, fg_color=KLEUR_WIS,
                          command=lambda u=r["url"]: self._wis_blok(u)).pack(side="left", padx=4)
        else:
            ctk.CTkButton(kop, text="wis", width=48, fg_color=KLEUR_WIS,
                          command=lambda u=r["url"]: self._wis_een(u)).pack(side="left", padx=4)

        ctk.CTkLabel(parent, text=r["url"], text_color="gray", anchor="w",
                     font=ctk.CTkFont(size=10)).pack(fill="x", padx=14)

        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(2, 8))
        body.grid_columnconfigure(0, weight=1, uniform="kol")
        body.grid_columnconfigure(1, weight=1, uniform="kol")
        ctk.CTkLabel(body, text=r["samenvatting"] or "—", wraplength=440, justify="left",
                     anchor="nw").grid(row=0, column=0, sticky="nwe", padx=(0, 8))
        ctk.CTkLabel(body, text=r["oordeel"] or "—", wraplength=440, justify="left",
                     anchor="nw", text_color="#cfcfcf").grid(row=0, column=1, sticky="nwe")

    def _subrij(self, parent, s):
        # Eén strakke regel per video: aanvinkvakje, klikbare titel, kopieer, wis.
        klein = ctk.CTkFont(size=11)
        rij = ctk.CTkFrame(parent, fg_color="transparent", height=26)
        rij.pack(fill="x", padx=(28, 6), pady=0)
        rij.pack_propagate(False)
        var = ctk.BooleanVar(value=(s["status"] == "bewaard"))
        ctk.CTkCheckBox(rij, text="", width=22, checkbox_width=16, checkbox_height=16,
                        variable=var,
                        command=lambda u=s["url"], v=var: self._bewaar_toggle(u, v)
                        ).pack(side="left")
        ctk.CTkButton(rij, text=f"🎬  {(s['titel'] or s['url'])[:110]}", anchor="w",
                      height=24, font=klein, fg_color="transparent",
                      text_color=KLEUR_LINK, hover=False,
                      command=lambda u=s["url"]: self._open(u)
                      ).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(rij, text="kopieer", width=58, height=24, font=klein,
                      command=lambda u=s["url"]: self._kopieer(u)).pack(side="left", padx=2)
        ctk.CTkButton(rij, text="wis", width=40, height=24, font=klein, fg_color=KLEUR_WIS,
                      command=lambda u=s["url"]: self._wis_een(u)).pack(side="left", padx=2)


if __name__ == "__main__":
    App().mainloop()
