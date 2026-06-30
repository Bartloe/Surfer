"""
gui — het scherm van de stand-alone Surfer-app (customtkinter).

Versie: 1.0
Reden:  Eerste versie — profielen onderhouden, zoeken, resultaten tonen/afhandelen.
Datum:  2026-06-30 19:18 (NL)

- Bovenin: profiel kiezen/bewerken/nieuw, drempel + aantal, en de zoekknop.
- Resultaten per blok: een pagina met daaronder de video's die erop staan (suburls);
  losse video-treffers staan op zichzelf.
- Per regel: aankruisvak (bewaren), klikbare url (opent browser + markeert 'bezocht'),
  het DeepSeek-oordeel rechts, de samenvatting links.
- Bulk: 'wis blok' (pagina + suburls) en 'wis alles van laatste run'.
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

        self._bouw_bovenbalk()
        self._bouw_resultaten()
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
        self._status("Bezig met zoeken…")
        threading.Thread(target=self._run_thread,
                         args=(self.profiel_var.get(), drempel, maxn), daemon=True).start()

    def _run_thread(self, profiel, drempel, maxn):
        def log(m):
            self.after(0, self._status, m)

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
        webbrowser.open(url)
        if self.winkel:
            self.winkel.zet_status(url, "bezocht")
            self.winkel.bewaar()
            self._teken()

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
        if not self.winkel:
            return
        actief = self.winkel.actieve()
        paginas = [r for r in actief if r["type"] == "pagina"]
        videos = [r for r in actief if r["type"] == "video"]
        suburls = [r for r in actief if r["type"] == "suburl"]
        per_ouder: dict[str, list] = {}
        for s in suburls:
            per_ouder.setdefault(s.get("parent_url"), []).append(s)

        getoond = set()
        for p in paginas:
            blok = self._blok()
            self._hoofdrij(blok, p, wis_blok=True)
            for s in per_ouder.get(p["url"], []):
                self._subrij(blok, s)
                getoond.add(s["url"])
        for v in videos:
            self._hoofdrij(self._blok(), v, wis_blok=False)
        for s in suburls:                       # wees-suburls (ouder al weg)
            if s["url"] not in getoond:
                self._hoofdrij(self._blok(), s, wis_blok=False)

        if not actief:
            ctk.CTkLabel(self.lijst, text="(nog geen resultaten — kies een profiel en zoek)"
                         ).pack(pady=20)

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
        if wis_blok:
            ctk.CTkButton(kop, text="wis blok", width=72, fg_color=KLEUR_WIS,
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
        rij = ctk.CTkFrame(parent, fg_color="transparent")
        rij.pack(fill="x", padx=(34, 6), pady=1)
        var = ctk.BooleanVar(value=(s["status"] == "bewaard"))
        ctk.CTkCheckBox(rij, text="bewaar", width=70, variable=var,
                        command=lambda u=s["url"], v=var: self._bewaar_toggle(u, v)
                        ).pack(side="left")
        ctk.CTkButton(rij, text=f"🎬  {(s['titel'] or s['url'])[:95]}", anchor="w",
                      fg_color="transparent", text_color=KLEUR_LINK, hover=False,
                      command=lambda u=s["url"]: self._open(u)
                      ).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(rij, text="wis", width=48, fg_color=KLEUR_WIS,
                      command=lambda u=s["url"]: self._wis_een(u)).pack(side="left", padx=4)


if __name__ == "__main__":
    App().mainloop()
