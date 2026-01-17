#!/bin/bash

# Aeternis Backend - Start Script
# Questo script avvia il server di sviluppo (usa sempre questo)

set -e  # Exit on error

echo "🚀 Aeternis Backend - Avvio Server"
echo "==================================="
echo ""

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verifica virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment non trovato!${NC}"
    echo "Esegui prima: ./setup.sh"
    exit 1
fi

# 2. Attiva virtual environment
echo "🔌 Attivazione virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment attivato${NC}"
echo ""

# 3. Imposta settings module
export DJANGO_SETTINGS_MODULE=config.settings.local
echo -e "${GREEN}✅ Settings module: config.settings.local${NC}"
echo ""

# 4. Verifica migrazioni
echo "🔍 Verifica migrazioni..."
python3 manage.py makemigrations --check --dry-run > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Migrazioni pendenti trovate. Applicazione automatica...${NC}"
    python3 manage.py makemigrations
    python3 manage.py migrate
    echo -e "${GREEN}✅ Migrazioni applicate${NC}"
fi
echo ""

# 5. Avvia server
echo "🌐 Avvio server Django..."
echo -e "${GREEN}✅ Server disponibile su: http://localhost:8000${NC}"
echo ""
echo "Premi Ctrl+C per fermare il server"
echo ""

python3 manage.py runserver
