#!/bin/bash

# Proje dizinine git
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================="
echo "  AI Code Reviewer Başlatılıyor...       "
echo "=========================================="

# Zaten çalışan süreçler varsa temizle
pkill -f "uvicorn api:app" 2>/dev/null
pkill -f "next dev" 2>/dev/null

# 1. FastAPI Sunucusunu Başlat (Port 8000)
echo "[1/3] FastAPI Backend başlatılıyor (Port 8000)..."
source venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!

# FastAPI'nin uyanmasını bekle
sleep 2

# 2. Next.js Frontend Sunucusunu Başlat (Port 3000)
echo "[2/3] Next.js Frontend başlatılıyor (Port 3000)..."
cd frontend
npm run dev -- -p 3000 > /dev/null 2>&1 &
FRONTEND_PID=$!

# Next.js'in hazırlanmasını bekle
sleep 3

# 3. Tarayıcıda Otomatik Aç
echo "[3/3] Tarayıcı açılıyor: http://localhost:3000"
open "http://localhost:3000"

echo ""
echo "------------------------------------------"
echo "  AI Code Reviewer Aktif!                "
echo "  Kapatmak için CTRL+C yapın.            "
echo "------------------------------------------"

# Script açık kaldığı sürece çalışmaya devam etsin, kapatılınca süreçleri sonlandırsın
trap "echo 'Sunucular kapatılıyor...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; pkill -f 'uvicorn api:app'; pkill -f 'next dev'; exit" INT TERM EXIT

wait
