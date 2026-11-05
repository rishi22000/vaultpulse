import os
import datetime
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_db, init_db
from app.storage import format_file_size, format_duration, save_upload_file, UPLOAD_DIR, BASE_DIR

app = FastAPI(
    title="VaultPulse",
    description="Open-Source DocSend & Secure Asset Vault by Neelbyte Websolution",
    version="1.0.0",
    contact={"name": "Neelbyte Websolution"}
)

# Mount static and templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# Register custom Jinja filters
templates.env.filters["format_size"] = format_file_size
templates.env.filters["format_duration"] = format_duration

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "VaultPulse", "version": "1.0.0"}

# -------------------------------------------------------------
# DASHBOARD & ADMIN PAGES
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    # KPI Aggregates
    cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'active'")
    total_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM document_visits")
    total_views = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(AVG(duration_seconds), 0) FROM document_visits")
    avg_duration = int(cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM deliverables WHERE status = 'active'")
    active_deliverables = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(downloads_count), 0) FROM deliverables")
    total_downloads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proposals WHERE status = 'accepted'")
    accepted_proposals = cursor.fetchone()[0]

    # Documents List
    cursor.execute("""
    SELECT d.*, 
           (SELECT COUNT(*) FROM document_visits WHERE document_id = d.id) as real_visits,
           (SELECT COALESCE(AVG(duration_seconds), 0) FROM document_visits WHERE document_id = d.id) as doc_avg_dur
    FROM documents d
    ORDER BY created_at DESC
    """)
    documents = [dict(row) for row in cursor.fetchall()]

    # Deliverables List
    cursor.execute("SELECT * FROM deliverables ORDER BY created_at DESC LIMIT 5")
    deliverables = [dict(row) for row in cursor.fetchall()]

    # Recent Activity Stream
    cursor.execute("""
    SELECT v.*, d.title as doc_title
    FROM document_visits v
    JOIN documents d ON v.document_id = d.id
    ORDER BY v.started_at DESC
    LIMIT 6
    """)
    recent_visits = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse(request, "dashboard.html", {
        "kpi": {
            "total_docs": total_docs,
            "total_views": total_views,
            "avg_duration": avg_duration,
            "active_deliverables": active_deliverables,
            "total_downloads": total_downloads,
            "accepted_proposals": accepted_proposals,
        },
        "documents": documents,
        "deliverables": deliverables,
        "recent_visits": recent_visits,
        "active_tab": "dashboard"
    })

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT d.*, 
           (SELECT COUNT(*) FROM document_visits WHERE document_id = d.id) as real_visits,
           (SELECT COALESCE(AVG(duration_seconds), 0) FROM document_visits WHERE document_id = d.id) as doc_avg_dur
    FROM documents d
    ORDER BY created_at DESC
    """)
    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(request, "documents.html", {
        "documents": docs,
        "active_tab": "documents"
    })

@app.get("/documents/{doc_id}", response_class=HTMLResponse)
async def document_analytics_page(request: Request, doc_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    doc = dict(doc)

    # Page-by-page stats
    cursor.execute("""
    SELECT page_number, total_seconds, view_count
    FROM document_page_stats
    WHERE document_id = ?
    ORDER BY page_number ASC
    """, (doc_id,))
    page_stats = [dict(row) for row in cursor.fetchall()]

    # If page_stats is empty, fill with defaults
    if not page_stats:
        for p in range(1, (doc.get("total_pages") or 5) + 1):
            page_stats.append({"page_number": p, "total_seconds": 0, "view_count": 0, "avg_seconds": 0})
    else:
        for ps in page_stats:
            v_cnt = ps["view_count"] or 1
            ps["avg_seconds"] = int(ps["total_seconds"] / v_cnt)

    # Visitor log
    cursor.execute("""
    SELECT * FROM document_visits
    WHERE document_id = ?
    ORDER BY started_at DESC
    """, (doc_id,))
    visits = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse(request, "doc_detail.html", {
        "doc": doc,
        "page_stats": page_stats,
        "visits": visits,
        "active_tab": "documents"
    })

@app.get("/deliverables", response_class=HTMLResponse)
async def deliverables_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deliverables ORDER BY created_at DESC")
    deliverables = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(request, "deliverables.html", {
        "deliverables": deliverables,
        "active_tab": "deliverables"
    })

@app.get("/proposals", response_class=HTMLResponse)
async def proposals_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposals ORDER BY created_at DESC")
    proposals = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(request, "proposals.html", {
        "proposals": proposals,
        "active_tab": "proposals"
    })

# -------------------------------------------------------------
# CREATE / UPLOAD ACTIONS
# -------------------------------------------------------------

@app.post("/api/documents/create")
async def create_document(
    title: str = Form(...),
    description: str = Form(""),
    access_type: str = Form("open"),
    passcode: Optional[str] = Form(None),
    allow_download: bool = Form(False),
    watermark_enabled: bool = Form(False),
    total_pages: int = Form(6),
    file: UploadFile = File(...)
):
    rel_path, safe_name, size, _ = await save_upload_file(file, custom_prefix="deck")
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO documents (
        id, title, description, file_path, file_name, file_size, total_pages,
        access_type, passcode, allow_download, watermark_enabled, created_at, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (
        doc_id, title, description, rel_path, safe_name, size, total_pages,
        access_type, passcode if access_type == "passcode" else None,
        1 if allow_download else 0,
        1 if watermark_enabled else 0,
        now
    ))

    # Initialize empty page stats
    for p in range(1, total_pages + 1):
        cursor.execute("""
        INSERT INTO document_page_stats (document_id, page_number, total_seconds, view_count)
        VALUES (?, ?, 0, 0)
        """, (doc_id, p))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/documents/{doc_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/deliverables/create")
async def create_deliverable(
    title: str = Form(...),
    description: str = Form(""),
    passcode: Optional[str] = Form(None),
    max_downloads: int = Form(5),
    file: UploadFile = File(...)
):
    rel_path, safe_name, size, _ = await save_upload_file(file, custom_prefix="pkg")
    deliv_id = f"dl_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO deliverables (
        id, title, description, file_path, file_name, file_size, passcode, max_downloads, created_at, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (
        deliv_id, title, description, rel_path, safe_name, size,
        passcode.strip() if passcode else None,
        max_downloads,
        now
    ))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/deliverables", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/proposals/create")
async def create_proposal(
    client_name: str = Form(...),
    client_email: str = Form(...),
    project_title: str = Form(...),
    scope_summary: str = Form(""),
    total_amount: str = Form(...)
):
    prop_id = f"prop_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO proposals (
        id, client_name, client_email, project_title, scope_summary, total_amount, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (prop_id, client_name, client_email, project_title, scope_summary, total_amount, now))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/proposals", status_code=status.HTTP_303_SEE_OTHER)

# -------------------------------------------------------------
# CLIENT-FACING VIEWER (DocSend Style)
# -------------------------------------------------------------

@app.get("/v/{doc_id}", response_class=HTMLResponse)
async def client_view_document(request: Request, doc_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Presentation or document not found")
    doc = dict(doc)
    conn.close()

    session_id = request.cookies.get(f"vp_session_{doc_id}")
    viewer_email = request.cookies.get(f"vp_email_{doc_id}")
    unlocked_pass = request.cookies.get(f"vp_unlocked_{doc_id}")

    # Check access guards
    gate_required = False
    gate_type = None

    if doc["access_type"] == "email_gate" and not viewer_email:
        gate_required = True
        gate_type = "email"
    elif doc["access_type"] == "passcode" and unlocked_pass != doc["passcode"]:
        gate_required = True
        gate_type = "passcode"

    return templates.TemplateResponse(request, "view_document.html", {
        "doc": doc,
        "gate_required": gate_required,
        "gate_type": gate_type,
        "session_id": session_id or uuid.uuid4().hex[:12],
        "viewer_email": viewer_email or ""
    })

@app.post("/api/v/{doc_id}/unlock")
async def client_unlock_gate(
    doc_id: str,
    email: Optional[str] = Form(None),
    passcode: Optional[str] = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    doc = dict(doc)

    response = RedirectResponse(url=f"/v/{doc_id}", status_code=status.HTTP_303_SEE_OTHER)

    if doc["access_type"] == "email_gate":
        if not email or "@" not in email:
            conn.close()
            return RedirectResponse(url=f"/v/{doc_id}?error=invalid_email", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key=f"vp_email_{doc_id}", value=email.strip().lower(), max_age=86400 * 30)

    elif doc["access_type"] == "passcode":
        if passcode != doc["passcode"]:
            conn.close()
            return RedirectResponse(url=f"/v/{doc_id}?error=invalid_passcode", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key=f"vp_unlocked_{doc_id}", value=passcode, max_age=86400 * 30)

    # Initialize visit session cookie
    sess_id = uuid.uuid4().hex[:12]
    response.set_cookie(key=f"vp_session_{doc_id}", value=sess_id, max_age=86400 * 30)

    # Log initial visit
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO document_visits (
        document_id, session_id, viewer_email, viewer_ip, device_type,
        started_at, last_heartbeat, duration_seconds, pages_viewed, completed, downloaded
    ) VALUES (?, ?, ?, '127.0.0.1', 'Desktop Browser', ?, ?, 0, 1, 0, 0)
    """, (doc_id, sess_id, email.strip().lower() if email else 'Verified Reader', now, now))

    cursor.execute("UPDATE documents SET views_count = views_count + 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    return response

@app.post("/api/v/{doc_id}/heartbeat")
async def client_heartbeat(
    doc_id: str,
    session_id: str = Form(...),
    page_number: int = Form(1),
    seconds_active: int = Form(2),
    pages_seen: int = Form(1)
):
    """
    Called every few seconds from the client viewer.
    Updates total duration, page-by-page seconds, and completion status.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    cursor = conn.cursor()

    # Update visit session
    cursor.execute("""
    UPDATE document_visits
    SET duration_seconds = duration_seconds + ?,
        last_heartbeat = ?,
        pages_viewed = MAX(pages_viewed, ?)
    WHERE document_id = ? AND session_id = ?
    """, (seconds_active, now, pages_seen, doc_id, session_id))

    # Update page stats
    cursor.execute("""
    INSERT INTO document_page_stats (document_id, page_number, total_seconds, view_count)
    VALUES (?, ?, ?, 1)
    ON CONFLICT(document_id, page_number) DO UPDATE SET
        total_seconds = total_seconds + excluded.total_seconds,
        view_count = view_count + 1
    """, (doc_id, page_number, seconds_active))

    # Update document aggregate
    cursor.execute("""
    UPDATE documents
    SET avg_duration_sec = (
        SELECT COALESCE(AVG(duration_seconds), 0)
        FROM document_visits
        WHERE document_id = ?
    )
    WHERE id = ?
    """, (doc_id, doc_id))

    conn.commit()
    conn.close()

    return {"status": "ok", "recorded_seconds": seconds_active}

@app.get("/v/{doc_id}/download")
async def download_document_file(doc_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = dict(doc)

    if not doc["allow_download"]:
        raise HTTPException(status_code=403, detail="Download disabled by owner")

    file_path = BASE_DIR / doc["file_path"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical file missing on server")

    return FileResponse(
        path=str(file_path),
        filename=doc["file_name"],
        media_type="application/octet-stream"
    )

# -------------------------------------------------------------
# CLIENT-FACING DELIVERABLE DOWNLOAD (WeTransfer Style)
# -------------------------------------------------------------

@app.get("/d/{deliv_id}", response_class=HTMLResponse)
async def client_view_deliverable(request: Request, deliv_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deliverables WHERE id = ?", (deliv_id,))
    deliv = cursor.fetchone()
    conn.close()

    if not deliv:
        raise HTTPException(status_code=404, detail="Asset delivery link not found or expired")
    deliv = dict(deliv)

    unlocked = False
    if not deliv["passcode"]:
        unlocked = True
    else:
        cookie_val = request.cookies.get(f"vp_dl_unlock_{deliv_id}")
        if cookie_val == deliv["passcode"]:
            unlocked = True

    return templates.TemplateResponse(request, "download_file.html", {
        "deliv": deliv,
        "unlocked": unlocked
    })

@app.post("/api/d/{deliv_id}/unlock")
async def client_unlock_deliverable(deliv_id: str, passcode: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deliverables WHERE id = ?", (deliv_id,))
    deliv = cursor.fetchone()
    conn.close()

    if not deliv:
        raise HTTPException(status_code=404, detail="Not found")
    deliv = dict(deliv)

    if passcode.strip() != deliv["passcode"]:
        return RedirectResponse(url=f"/d/{deliv_id}?error=invalid_passcode", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url=f"/d/{deliv_id}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key=f"vp_dl_unlock_{deliv_id}", value=passcode.strip(), max_age=86400 * 7)
    return response

@app.get("/d/{deliv_id}/download")
async def process_deliverable_download(request: Request, deliv_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deliverables WHERE id = ?", (deliv_id,))
    deliv = cursor.fetchone()

    if not deliv:
        conn.close()
        raise HTTPException(status_code=404, detail="Deliverable not found")
    deliv = dict(deliv)

    if deliv["status"] == "download_limit_reached" or deliv["downloads_count"] >= deliv["max_downloads"]:
        conn.close()
        raise HTTPException(status_code=410, detail="Download limit exceeded for this secure link")

    if deliv["passcode"]:
        cookie_val = request.cookies.get(f"vp_dl_unlock_{deliv_id}")
        if cookie_val != deliv["passcode"]:
            conn.close()
            return RedirectResponse(url=f"/d/{deliv_id}?error=auth_required")

    file_path = BASE_DIR / deliv["file_path"]
    if not file_path.exists():
        conn.close()
        raise HTTPException(status_code=404, detail="File missing on disk")

    # Increment download count
    new_count = deliv["downloads_count"] + 1
    new_status = "download_limit_reached" if new_count >= deliv["max_downloads"] else "active"

    cursor.execute("""
    UPDATE deliverables
    SET downloads_count = ?, status = ?
    WHERE id = ?
    """, (new_count, new_status, deliv_id))
    conn.commit()
    conn.close()

    return FileResponse(
        path=str(file_path),
        filename=deliv["file_name"],
        media_type="application/octet-stream"
    )

# -------------------------------------------------------------
# CLIENT-FACING PROPOSAL SIGN-OFF
# -------------------------------------------------------------

@app.get("/p/{prop_id}", response_class=HTMLResponse)
async def client_view_proposal(request: Request, prop_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposals WHERE id = ?", (prop_id,))
    prop = cursor.fetchone()
    conn.close()

    if not prop:
        raise HTTPException(status_code=404, detail="Proposal not found")
    prop = dict(prop)

    return templates.TemplateResponse(request, "proposal_view.html", {
        "prop": prop
    })

@app.post("/api/p/{prop_id}/sign")
async def client_sign_proposal(prop_id: str, signature_name: str = Form(...)):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE proposals
    SET status = 'accepted',
        accepted_at = ?,
        signature_name = ?
    WHERE id = ?
    """, (now, signature_name.strip(), prop_id))
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/p/{prop_id}?signed=success", status_code=status.HTTP_303_SEE_OTHER)
