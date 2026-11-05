<div align="center">

  <img src="app/static/brand/logo.svg" alt="VaultPulse Logo" width="320">

  <p align="center">
    <strong>Open-Source Document Intelligence &amp; Zero-Knowledge Client Asset Vault</strong><br>
    The self-hosted, privacy-first alternative to <strong>DocSend ($65/mo)</strong> and <strong>WeTransfer Pro ($19/mo)</strong>.
  </p>

  <p align="center">
    <!-- Official Hostinger Partner Badge -->
    <a href="https://www.hostinger.com/in?REFERRALCODE=HDZRISHABI2O" target="_blank" rel="noopener noreferrer">
      <img src="assets/hostinger/svg/Badge_brand_dark.svg" alt="Deploy to Hostinger" height="42">
    </a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Author-Neelbyte_Websolution-emerald?style=flat-square" alt="Author">
    <img src="https://img.shields.io/badge/CI_Tests-11%2F11_Passing-emerald?style=flat-square" alt="Tests">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
    <img src="https://img.shields.io/badge/Architecture-SQLite_WAL-blue?style=flat-square" alt="DB">
    <img src="https://img.shields.io/badge/Docker-Ready-cyan?style=flat-square" alt="Docker">
    <img src="https://img.shields.io/badge/Hostinger_VPS-Optimized-purple?style=flat-square" alt="Hostinger">
  </p>

</div>

---

### Why VaultPulse?

| Feature | DocSend ($65/user/mo) | WeTransfer ($19/mo) | **VaultPulse (Self-Hosted)** |
| :--- | :---: | :---: | :---: |
| **Slide-by-Slide Time Analytics** | ✅ | ❌ | **✅ Included** |
| **Dynamic Email Watermarking** | ✅ ($150+ tier) | ❌ | **✅ Included (Anti-leak)** |
| **Work Email Access Gate** | ✅ | ❌ | **✅ Included** |
| **Passcode Protection** | ✅ | ✅ | **✅ Included** |
| **Auto-Destruct & Quotas** | ❌ | ✅ | **✅ Included** |
| **Client Proposals & Sign-off** | ❌ (DocuSign $40/mo) | ❌ | **✅ Included** |
| **Monthly Subscription** | **$780 / year** | **$228 / year** | **$0 / year (Free Forever)** |
| **Data Privacy & Ownership** | Third-party cloud | Third-party cloud | **100% on your own VPS** |

---

### Core Architecture & Features

* **Slide-by-Slide Real-Time Analytics:** Tracks exactly how many seconds investors or clients spend on each individual slide (e.g., Financials, Team, Pricing).
* **Anti-Leak Dynamic Watermarking:** Dynamically stamps the reader's email address across every page to prevent unauthorized screenshots or forwarding.
* **Granular Access Control:** Protect any document with Email Verification Gates, Secret Passcodes, or Link Expiration dates.
* **Auto-Destruct Deliverables Locker:** Deliver high-res assets, source code, and client bundles with self-destructing download limits.
* **1-Click Proposal Sign-off:** Send formal scope quotes with digital client authorization and timestamped audit log.
* **Zero External Dependencies:** Built with FastAPI + SQLite (WAL mode). No heavy external databases required.

---

### 1-Click Hostinger VPS Deployment

Deploying your own instance of VaultPulse takes under 60 seconds on Hostinger:

1. Click the **[Deploy to Hostinger](https://www.hostinger.com/in?REFERRALCODE=HDZRISHABI2O)** badge above.
2. Select an **Ubuntu 24.04 VPS** plan (Standard VPS 1 or VPS 2).
3. Connect via SSH and run:

```bash
git clone https://github.com/rishi22000/vaultpulse.git
cd vaultpulse
chmod +x hostinger-deploy.sh
./hostinger-deploy.sh
```

Your instance will immediately start at `http://YOUR_VPS_IP:8000`.

---

### Local Quickstart

```bash
# 1. Clone repository
git clone https://github.com/rishi22000/vaultpulse.git
cd vaultpulse

# 2. Setup Virtual Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start Server
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser.

---

### Author & Credits

Designed, engineered, and maintained by **Neelbyte Websolution**.
* Website / Inquiries: [Neelbyte Websolution](https://github.com/rishi22000)
* Purpose: Production-grade self-hosted software built for high reliability, zero data leakage, and seamless 1-click cloud deployment.

---

### License
Released under the permissive **MIT License** &copy; 2026 **Neelbyte Websolution**. Free for personal and commercial usage.
