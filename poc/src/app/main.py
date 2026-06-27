from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from src.app.services.db import get_connection
from pydantic import BaseModel
import threading
import os
import sqlite3
from pathlib import Path
import csv
import io
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
templates = Jinja2Templates(directory="src/app/templates")


# ---------------------------------------------------------
# HULPFUNCTIE: actief profiel ophalen (als dict)
# ---------------------------------------------------------
def get_active_profile():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, profile_text FROM taste_profiles WHERE is_active = 1 LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "name": row["name"], "profile_text": row["profile_text"]}
    return None


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    active = get_active_profile()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "active_profile": active}
    )


# ---------------------------------------------------------
# TAB 1 — Relevante resultaten (alleen niet-gezien)
# ---------------------------------------------------------
@app.get("/tab1", response_class=HTMLResponse)
def tab1(request: Request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, summary, match_score, engine, url, snippet
        FROM discoveries
        WHERE user_status IS NULL OR user_status != 'Gezien'
        ORDER BY match_score DESC
    """)
    rows = cur.fetchall()
    conn.close()

    active = get_active_profile()

    return templates.TemplateResponse(
        "tab1_relevant.html",
        {"request": request, "results": rows, "active_profile": active}
    )


# ---------------------------------------------------------
# TAB 2 — Scrape mislukt (alleen niet-gezien)
# ---------------------------------------------------------
@app.get("/tab2", response_class=HTMLResponse)
def tab2(request: Request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, url, reason, engine
        FROM failed_scrapes
        WHERE user_status IS NULL OR user_status != 'Gezien'
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    active = get_active_profile()

    return templates.TemplateResponse(
        "tab2_failed.html",
        {"request": request, "failed": rows, "active_profile": active}
    )


# ---------------------------------------------------------
# SMAAKPROFIELEN (overzicht + beheer)
# ---------------------------------------------------------
@app.get("/profiles", response_class=HTMLResponse)
def profiles(request: Request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, is_active, profile_text FROM taste_profiles ORDER BY id ASC")
    profiles = cur.fetchall()
    active = get_active_profile()
    search_terms = []
    if active:
        cur.execute("SELECT term FROM search_terms WHERE profile_id = ?", (active["id"],))
        search_terms = [r[0] for r in cur.fetchall()]
    conn.close()
    return templates.TemplateResponse(
        "taste_profiles.html",
        {
            "request": request,
            "profiles": profiles,
            "active_profile": active,
            "search_terms": search_terms
        }
    )


@app.post("/profiles/create")
def create_profile(name: str = Form(...)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO taste_profiles (name, description, is_active, profile_text) VALUES (?, '', 0, '')", (name,))
    conn.commit()
    conn.close()
    return JSONResponse({"status": "ok"})


@app.post("/profiles/activate")
def activate_profile(profile_id: int = Form(...)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE taste_profiles SET is_active = 0")
    cur.execute("UPDATE taste_profiles SET is_active = 1 WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"status": "ok"})


@app.post("/profiles/update-text")
def update_profile_text(profile_id: int = Form(...), text: str = Form(...)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE taste_profiles SET profile_text = ? WHERE id = ?", (text, profile_id))
    conn.commit()
    conn.close()
    return JSONResponse({"status": "ok"})


@app.post("/profiles/add-search-terms")
def add_search_terms(profile_id: int = Form(...), search_terms: str = Form(...)):
    conn = get_connection()
    cur = conn.cursor()
    for term in search_terms.strip().splitlines():
        term = term.strip()
        if term:
            cur.execute("INSERT INTO search_terms (profile_id, term) VALUES (?, ?)", (profile_id, term))
    conn.commit()
    conn.close()
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------
@app.get("/export-modal", response_class=HTMLResponse)
def export_modal(request: Request):
    return templates.TemplateResponse("export_modal.html", {"request": request})


@app.api_route("/export", methods=["GET", "POST"])
def export_data():
    return JSONResponse({"status": "exported"})


# ---------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------
@app.get("/upload-modal", response_class=HTMLResponse)
def upload_modal(request: Request):
    return templates.TemplateResponse("upload_modal.html", {"request": request})


@app.api_route("/upload-file", methods=["GET", "POST"])
async def upload_file(file: UploadFile = None):
    if file is None:
        return JSONResponse({"error": "No file uploaded"})
    content = await file.read()
    return JSONResponse({"filename": file.filename, "size": len(content)})


# ---------------------------------------------------------
# API: START CRAWLER
# ---------------------------------------------------------
class CrawlRequest(BaseModel):
    max_results: int = 10

# Import wordt hier uitgevoerd, niet bovenaan, om circular import te voorkomen
@app.post("/api/start-crawl")
def start_crawl(request: CrawlRequest):
    from src.app.crawler.runner.runner import Runner  # <-- verplaatst

    def run_crawler():
        try:
            runner = Runner()
            runner.run(max_results=request.max_results)
        except Exception as e:
            print(f"Crawler error: {e}")

    thread = threading.Thread(target=run_crawler)
    thread.start()
    return JSONResponse({"status": "ok", "message": f"Crawler gestart met max {request.max_results} resultaten per zoekterm."})


# ---------------------------------------------------------
# API: EXPORT URLS EN STATUS UPDATE
# ---------------------------------------------------------
class StatusUpdateRequest(BaseModel):
    ids: list[int]
    table: str  # "discoveries" of "failed_scrapes"

def get_next_export_filename() -> str:
    base = "urls"
    ext = ".txt"
    counter = 0
    while True:
        if counter == 0:
            name = f"{base}{ext}"
        else:
            name = f"{base}{counter}{ext}"
        if not os.path.exists(name):
            return name
        counter += 1

@app.post("/api/export-urls")
def export_urls(data: StatusUpdateRequest):
    if data.table not in ["discoveries", "failed_scrapes"]:
        return JSONResponse({"error": "Ongeldige tabel"}, status_code=400)
    if not data.ids:
        return JSONResponse({"error": "Geen IDs opgegeven"}, status_code=400)

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in data.ids)
    query = f"SELECT url FROM {data.table} WHERE id IN ({placeholders})"
    cur.execute(query, data.ids)
    urls = [row[0] for row in cur.fetchall()]

    update_query = f"UPDATE {data.table} SET user_status = 'Interessant' WHERE id IN ({placeholders})"
    cur.execute(update_query, data.ids)
    conn.commit()
    conn.close()

    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    filename = export_dir / get_next_export_filename()
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))

    return JSONResponse({"status": "ok", "message": f"{len(urls)} URLs geëxporteerd naar {filename.name}"})


@app.post("/api/mark-seen")
def mark_seen(data: StatusUpdateRequest):
    if data.table not in ["discoveries", "failed_scrapes"]:
        return JSONResponse({"error": "Ongeldige tabel"}, status_code=400)
    if not data.ids:
        return JSONResponse({"error": "Geen IDs opgegeven"}, status_code=400)

    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in data.ids)
    query = f"UPDATE {data.table} SET user_status = 'Gezien' WHERE id IN ({placeholders})"
    cur.execute(query, data.ids)
    conn.commit()
    conn.close()

    return JSONResponse({"status": "ok", "message": f"{len(data.ids)} records gemarkeerd als 'Gezien'."})


# ---------------------------------------------------------
# API: EXPORT ALLE DATA (CSV)
# ---------------------------------------------------------
@app.get("/api/export-all")
def export_all_data():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, url, title, snippet, summary, match_score, relevance_score, engine, profile_id, created_at, user_status
        FROM discoveries
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "url", "title", "snippet", "summary", "match_score", "relevance_score", "engine", "profile_id", "created_at", "user_status"])
    for row in rows:
        writer.writerow([row["id"], row["url"], row["title"], row["snippet"], row["summary"], row["match_score"], row["relevance_score"], row["engine"], row["profile_id"], row["created_at"], row["user_status"]])

    response = JSONResponse(content=output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=discoveries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Type"] = "text/csv"
    return response