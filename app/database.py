import sqlite3
import os
import datetime
from pathlib import Path

DB_PATH = os.environ.get("DATABASE_PATH", str(Path(__file__).parent.parent / "data" / "vaultpulse.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        total_pages INTEGER DEFAULT 1,
        access_type TEXT DEFAULT 'open', -- 'open', 'email_gate', 'passcode'
        passcode TEXT DEFAULT NULL,
        allow_download INTEGER DEFAULT 1,
        watermark_enabled INTEGER DEFAULT 1,
        expires_at TEXT DEFAULT NULL,
        views_count INTEGER DEFAULT 0,
        unique_viewers INTEGER DEFAULT 0,
        avg_duration_sec INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS document_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        viewer_email TEXT DEFAULT 'Anonymous Reader',
        viewer_ip TEXT DEFAULT '127.0.0.1',
        device_type TEXT DEFAULT 'Desktop',
        started_at TEXT NOT NULL,
        last_heartbeat TEXT NOT NULL,
        duration_seconds INTEGER DEFAULT 0,
        pages_viewed INTEGER DEFAULT 1,
        completed INTEGER DEFAULT 0,
        downloaded INTEGER DEFAULT 0,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS document_page_stats (
        document_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        total_seconds INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        PRIMARY KEY (document_id, page_number),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS deliverables (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        passcode TEXT DEFAULT NULL,
        max_downloads INTEGER DEFAULT 5,
        downloads_count INTEGER DEFAULT 0,
        expires_at TEXT DEFAULT NULL,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS proposals (
        id TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        client_email TEXT NOT NULL,
        project_title TEXT NOT NULL,
        scope_summary TEXT DEFAULT '',
        total_amount TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'declined'
        accepted_at TEXT DEFAULT NULL,
        signature_name TEXT DEFAULT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    seed_demo_data(conn)
    conn.close()

def seed_demo_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    if cursor.fetchone()[0] > 0:
        return  # already seeded

    now = datetime.datetime.now(datetime.timezone.utc)
    t_minus_1h = (now - datetime.timedelta(hours=1)).isoformat()
    t_minus_3h = (now - datetime.timedelta(hours=3)).isoformat()
    t_minus_1d = (now - datetime.timedelta(days=1)).isoformat()
    t_plus_7d = (now + datetime.timedelta(days=7)).isoformat()

    # 1. Pitch Deck Document (DocSend style)
    cursor.execute("""
    INSERT INTO documents (
        id, title, description, file_path, file_name, file_size, total_pages,
        access_type, passcode, allow_download, watermark_enabled, expires_at,
        views_count, unique_viewers, avg_duration_sec, created_at, status
    ) VALUES (
        'deck_series_a_pitch',
        'VaultPulse Series A Investor Presentation',
        'Confidential pitch deck detailing traction, unit economics, and 2027 market roadmap.',
        'uploads/sample_series_a_deck.pdf',
        'VaultPulse_Series_A_Confidential.pdf',
        4823440,
        8,
        'email_gate',
        NULL,
        0,
        1,
        ?,
        38,
        14,
        214,
        ?,
        'active'
    )
    """, (t_plus_7d, t_minus_1d))

    # Page-by-page stats for the pitch deck
    page_data = [
        (1, 480, 38),   # Title slide: 12.6s avg
        (2, 850, 36),   # Problem: 23.6s avg
        (3, 1420, 34),  # Solution: 41.7s avg
        (4, 2890, 32),  # Product Architecture & Tech Stack: 90.3s avg (High focus!)
        (5, 3450, 29),  # Traction & MRR Growth: 118.9s avg (Highest focus!)
        (6, 1980, 26),  # Competitor Matrix: 76.1s avg
        (7, 2100, 24),  # Financial Projections & Ask: 87.5s avg
        (8, 620, 22),   # Team & Contact: 28.1s avg
    ]
    for page, sec, views in page_data:
        cursor.execute("""
        INSERT INTO document_page_stats (document_id, page_number, total_seconds, view_count)
        VALUES ('deck_series_a_pitch', ?, ?, ?)
        """, (page, sec, views))

    # Recent visits
    visitors = [
        ('marc.a@sequoia-invest.example', '198.51.100.44', 'Desktop (macOS / Chrome)', t_minus_1h, 345, 8, 1),
        ('sarah.lin@accel-partners.example', '203.0.113.89', 'Desktop (Windows / Edge)', t_minus_3h, 280, 7, 1),
        ('elena.v@benchmark-capital.example', '192.0.2.11', 'Mobile (iOS / Safari)', t_minus_1d, 140, 5, 0),
    ]
    for email, ip, device, started, dur, pages, comp in visitors:
        cursor.execute("""
        INSERT INTO document_visits (
            document_id, session_id, viewer_email, viewer_ip, device_type,
            started_at, last_heartbeat, duration_seconds, pages_viewed, completed, downloaded
        ) VALUES (
            'deck_series_a_pitch', hex(randomblob(8)), ?, ?, ?, ?, ?, ?, ?, ?, 0
        )
        """, (email, ip, device, started, started, dur, pages, comp))

    # 2. Design System & Tech Spec Document
    cursor.execute("""
    INSERT INTO documents (
        id, title, description, file_path, file_name, file_size, total_pages,
        access_type, passcode, allow_download, watermark_enabled, expires_at,
        views_count, unique_viewers, avg_duration_sec, created_at, status
    ) VALUES (
        'spec_cloud_architecture',
        'Enterprise VPC & Security Blueprint v3.4',
        'Technical specification, zero-trust network diagrams, and API integration guide.',
        'uploads/sample_cloud_spec.pdf',
        'Enterprise_Security_Blueprint_2026.pdf',
        2340100,
        5,
        'passcode',
        'secure2026',
        1,
        0,
        NULL,
        19,
        9,
        168,
        ?,
        'active'
    )
    """, (t_minus_3h,))

    for p in range(1, 6):
        cursor.execute("""
        INSERT INTO document_page_stats (document_id, page_number, total_seconds, view_count)
        VALUES ('spec_cloud_architecture', ?, ?, ?)
        """, (p, 420 * p, 15 + p))

    # 3. Deliverables (WeTransfer style)
    cursor.execute("""
    INSERT INTO deliverables (
        id, title, description, file_path, file_name, file_size,
        passcode, max_downloads, downloads_count, expires_at, created_at, status
    ) VALUES (
        'dl_brand_assets_q4',
        'Acme Corp Brand Package & Vector Deliverables',
        'Master Figma exports, high-res 4K renders, vector brand guidelines, and typography bundle.',
        'uploads/sample_brand_assets.zip',
        'Acme_Brand_Master_Bundle_v2.zip',
        148892000,
        'acme2026',
        5,
        2,
        ?,
        ?,
        'active'
    )
    """, (t_plus_7d, t_minus_1d))

    cursor.execute("""
    INSERT INTO deliverables (
        id, title, description, file_path, file_name, file_size,
        passcode, max_downloads, downloads_count, expires_at, created_at, status
    ) VALUES (
        'dl_audit_compliance_report',
        'SOC-2 Type II Compliance & Penetration Test Report',
        'Audited pen-testing results, remediation verification, and certificate of compliance.',
        'uploads/sample_soc2_report.pdf',
        'SOC2_Type_II_Remediation_Report.pdf',
        5840000,
        NULL,
        3,
        3,
        ?,
        ?,
        'download_limit_reached'
    )
    """, (t_plus_7d, t_minus_1d))

    # 4. Proposal / Sign-off
    cursor.execute("""
    INSERT INTO proposals (
        id, client_name, client_email, project_title, scope_summary, total_amount, status, accepted_at, signature_name, created_at
    ) VALUES (
        'prop_fintech_cloud_migration',
        'Apex Global Capital',
        'procurement@apex-capital.example',
        'Cloud Infrastructure & Zero-Trust Modernization',
        'Complete Kubernetes migration, automated CI/CD pipeline rollout, SOC-2 readiness and staff enablement over 8 weeks.',
        '$24,500 USD',
        'accepted',
        ?,
        'Jonathan Vance (Managing Partner)',
        ?
    )
    """, (t_minus_1h, t_minus_1d))

    conn.commit()
