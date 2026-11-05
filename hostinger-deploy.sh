#!/usr/bin/env bash
# ==============================================================================
# VaultPulse 1-Click Hostinger VPS Deployment Script
# Author: Neelbyte Websolution
# ==============================================================================
set -e

echo "🚀 [VaultPulse] Deploying on Hostinger VPS..."

# 1. Update system & install docker if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker Engine & Compose..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# 2. Setup folders
mkdir -p data uploads
chmod -R 755 data uploads

# 3. Build & start container
echo "🏗️ Building VaultPulse container..."
docker compose down || true
docker compose up -d --build

echo "✅ VaultPulse is LIVE on your Hostinger VPS!"
echo "👉 Access your dashboard at: http://$(curl -s ifconfig.me):8000"
