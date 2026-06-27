"""
opslag — de enige, privé opslag van Surfer (SQLite).

Versie: 1.0
Reden:  Fase 0 — drie db-lagen (db/db_sync/storage) teruggebracht tot één.
Datum:  2026-06-27 17:56 (NL)

- Eigen werk van Surfer: runs (met status), vondsten, mislukte scrapes.
- Dit is GEEN afnemer-data; de afnemer leest hier nooit in.
- Geeft de pijplijn de haakjes voor start/stop/status:
    * start_run()  weigert een tweede run als er al één loopt.
    * vraag_stop() zet een vlag die de lopende run tussen items checkt.
    * laatste_run()/status geven inzicht zonder de run te storen.
- Elke db-aanroep zit in try/except met een betekenisvolle fout.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .vondst import Vondst

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    gestart_op    TEXT NOT NULL,
    geeindigd_op  TEXT,
    status        TEXT NOT NULL DEFAULT 'lopend',
    stop_gevraagd INTEGER NOT NULL DEFAULT 0,
    aantal_vondsten INTEGER NOT NULL DEFAULT 0,
    aantal_mislukt  INTEGER NOT NULL DEFAULT 0,
    notitie       TEXT
);
CREATE TABLE IF NOT EXISTS vondsten (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           INTEGER NOT NULL,
    titel            TEXT,
    bron_url         TEXT NOT NULL,
    samenvatting     TEXT,
    taal             TEXT,
    relevantie_reden TEXT,
    is_relevant      INTEGER NOT NULL DEFAULT 1,
    smaak_indicatie  REAL NOT NULL DEFAULT 0,
    externe_ids      TEXT,
    aangemaakt_op    TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
CREATE TABLE IF NOT EXISTS mislukte_scrapes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL,
    bron_url      TEXT NOT NULL,
    reden         TEXT,
    aangemaakt_op TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


def _nu() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Opslag:
    def __init__(self, db_pad: str | Path = "surfer_state.db"):
        self.db_pad = Path(db_pad)
        self._init_schema()

    @contextmanager
    def _verbind(self):
        # Sluit de verbinding altijd: anders blijft het db-bestand op Windows
        # vergrendeld (with op een sqlite3-connectie commit alleen, sluit niet).
        conn = sqlite3.connect(self.db_pad)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        try:
            with self._verbind() as conn:
                conn.executescript(SCHEMA)
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon opslag niet initialiseren ({self.db_pad}): {e}") from e

    # ---- runs: start / stop / status -------------------------------------
    def actieve_run(self) -> int | None:
        try:
            with self._verbind() as conn:
                rij = conn.execute(
                    "SELECT id FROM runs WHERE status = 'lopend' ORDER BY id DESC LIMIT 1"
                ).fetchone()
                return rij["id"] if rij else None
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon actieve run niet opvragen: {e}") from e

    def start_run(self) -> int:
        bestaand = self.actieve_run()
        if bestaand is not None:
            raise RuntimeError(f"Er loopt al een run (id {bestaand}); start geweigerd.")
        try:
            with self._verbind() as conn:
                cur = conn.execute(
                    "INSERT INTO runs (gestart_op, status) VALUES (?, 'lopend')", (_nu(),)
                )
                return cur.lastrowid
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon run niet starten: {e}") from e

    def beeindig_run(self, run_id: int, status: str, notitie: str = "") -> None:
        try:
            with self._verbind() as conn:
                conn.execute(
                    "UPDATE runs SET status = ?, geeindigd_op = ?, notitie = ? WHERE id = ?",
                    (status, _nu(), notitie, run_id),
                )
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon run {run_id} niet afsluiten: {e}") from e

    def vraag_stop(self, run_id: int | None = None) -> bool:
        run_id = run_id if run_id is not None else self.actieve_run()
        if run_id is None:
            return False
        try:
            with self._verbind() as conn:
                conn.execute("UPDATE runs SET stop_gevraagd = 1 WHERE id = ?", (run_id,))
            return True
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon stop niet vragen voor run {run_id}: {e}") from e

    def stop_gevraagd(self, run_id: int) -> bool:
        try:
            with self._verbind() as conn:
                rij = conn.execute(
                    "SELECT stop_gevraagd FROM runs WHERE id = ?", (run_id,)
                ).fetchone()
                return bool(rij and rij["stop_gevraagd"])
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon stop-vlag niet lezen voor run {run_id}: {e}") from e

    def laatste_run(self) -> dict | None:
        try:
            with self._verbind() as conn:
                rij = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
                return dict(rij) if rij else None
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon laatste run niet opvragen: {e}") from e

    # ---- vondsten / mislukte scrapes -------------------------------------
    def bewaar_vondst(self, run_id: int, vondst: Vondst) -> None:
        try:
            with self._verbind() as conn:
                conn.execute(
                    """INSERT INTO vondsten
                       (run_id, titel, bron_url, samenvatting, taal, relevantie_reden,
                        is_relevant, smaak_indicatie, externe_ids, aangemaakt_op)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, vondst.titel, vondst.bron_url, vondst.samenvatting,
                     vondst.taal, vondst.relevantie_reden, int(vondst.is_relevant),
                     vondst.smaak_indicatie, json.dumps(vondst.externe_ids), _nu()),
                )
                conn.execute(
                    "UPDATE runs SET aantal_vondsten = aantal_vondsten + 1 WHERE id = ?",
                    (run_id,),
                )
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon vondst niet opslaan: {e}") from e

    def bewaar_mislukt(self, run_id: int, bron_url: str, reden: str) -> None:
        try:
            with self._verbind() as conn:
                conn.execute(
                    "INSERT INTO mislukte_scrapes (run_id, bron_url, reden, aangemaakt_op) VALUES (?, ?, ?, ?)",
                    (run_id, bron_url, reden, _nu()),
                )
                conn.execute(
                    "UPDATE runs SET aantal_mislukt = aantal_mislukt + 1 WHERE id = ?",
                    (run_id,),
                )
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon mislukte scrape niet opslaan: {e}") from e

    def vondsten_van(self, run_id: int) -> list[dict]:
        try:
            with self._verbind() as conn:
                rijen = conn.execute(
                    "SELECT * FROM vondsten WHERE run_id = ? ORDER BY smaak_indicatie DESC, id ASC",
                    (run_id,),
                ).fetchall()
                return [dict(r) for r in rijen]
        except sqlite3.Error as e:
            raise RuntimeError(f"Kon vondsten niet opvragen: {e}") from e
