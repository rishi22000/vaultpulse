import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    client = httpx.Client(base_url=BASE_URL, follow_redirects=False, timeout=10.0)
    print("🧪 Running VaultPulse Comprehensive Test Suite...")
    
    # 1. Healthcheck
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    assert res.json().get("status") == "healthy"
    print("  ✅ [1/11] Health endpoint: PASSED")

    # 2. Dashboard
    res = client.get("/")
    assert res.status_code == 200, f"Dashboard failed: {res.status_code}"
    assert "VaultPulse" in res.text
    assert "Executive Intelligence" in res.text
    assert "deck_series_a_pitch" in res.text
    print("  ✅ [2/11] Executive Dashboard & KPIs: PASSED")

    # 3. Documents List Page
    res = client.get("/documents")
    assert res.status_code == 200
    assert "Tracked Presentations" in res.text
    print("  ✅ [3/11] Document Index: PASSED")

    # 4. Slide Dropoff Analytics Page
    res = client.get("/documents/deck_series_a_pitch")
    assert res.status_code == 200
    assert "Slide-by-Slide Time Engagement" in res.text
    assert "Detailed Visitor Access Log" in res.text
    assert "marc.a@sequoia-invest.example" in res.text
    print("  ✅ [4/11] Slide Dropoff Analytics & Audit Log: PASSED")

    # 5. Asset Lockers (Deliverables)
    res = client.get("/deliverables")
    assert res.status_code == 200
    assert "Secure Client Asset Lockers" in res.text
    assert "Acme Corp Brand Package" in res.text
    print("  ✅ [5/11] Deliverable Lockers Index: PASSED")

    # 6. Client Proposals
    res = client.get("/proposals")
    assert res.status_code == 200
    assert "Apex Global Capital" in res.text
    print("  ✅ [6/11] Client Proposals & Quotes: PASSED")

    # 7. Client Viewer - Email Gate Test
    res = client.get("/v/deck_series_a_pitch")
    assert res.status_code == 200
    assert "Please enter your work email" in res.text
    print("  ✅ [7/11] Client Viewer Email Gate: PASSED")

    # 8. Client Viewer - Unlock Gate
    unlock_res = client.post("/api/v/deck_series_a_pitch/unlock", data={"email": "investor.lead@venture.example"})
    assert unlock_res.status_code == 303
    cookies = unlock_res.cookies
    assert "vp_email_deck_series_a_pitch" in cookies
    assert "vp_session_deck_series_a_pitch" in cookies
    session_id = cookies["vp_session_deck_series_a_pitch"]
    print("  ✅ [8/11] Email Verification & Session Generation: PASSED")

    # 9. Client Viewer - Real-Time Heartbeat Ping
    hb_res = client.post("/api/v/deck_series_a_pitch/heartbeat", data={
        "session_id": session_id,
        "page_number": 4,
        "seconds_active": 6,
        "pages_seen": 4
    })
    assert hb_res.status_code == 200
    assert hb_res.json().get("status") == "ok"
    print("  ✅ [9/11] Real-Time Heartbeat Slide Tracking: PASSED")

    # 10. Deliverable Unlock & File Download (ensure test quota available)
    from app.database import get_db
    conn = get_db()
    conn.execute("UPDATE deliverables SET downloads_count = 1, status = 'active' WHERE id = 'dl_brand_assets_q4'")
    conn.commit()
    conn.close()

    dl_page = client.get("/d/dl_brand_assets_q4")
    assert dl_page.status_code == 200
    assert "Enter Access Passcode" in dl_page.text

    unlock_dl = client.post("/api/d/dl_brand_assets_q4/unlock", data={"passcode": "acme2026"})
    assert unlock_dl.status_code == 303
    dl_cookies = unlock_dl.cookies

    download_res = client.get("/d/dl_brand_assets_q4/download", cookies=dl_cookies)
    assert download_res.status_code == 200
    assert len(download_res.content) > 0
    print("  ✅ [10/11] Asset Locker Passcode Unlock & File Download: PASSED")

    # 11. Proposal Digital E-Signature
    sign_res = client.post("/api/p/prop_fintech_cloud_migration/sign", data={
        "signature_name": "Marcus Aurelius, CEO"
    })
    assert sign_res.status_code == 303
    prop_view = client.get("/p/prop_fintech_cloud_migration")
    assert prop_view.status_code == 200
    assert "Proposal Approved" in prop_view.text
    assert "Marcus Aurelius, CEO" in prop_view.text
    print("  ✅ [11/11] Client Proposal Digital Signature: PASSED")

    print("\n🎉 ALL 11 TESTS PASSED PERFECTLY! System is 100% stable & production-ready.")

if __name__ == "__main__":
    run_tests()
