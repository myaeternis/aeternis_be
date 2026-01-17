#!/bin/bash

# Aeternis Backend - Setup Script
# Questo script esegue il setup completo del backend (solo la prima volta)

set -e  # Exit on error

echo "🚀 Aeternis Backend - Setup Iniziale"
echo "===================================="
echo ""

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verifica Python
echo "📦 Verifica Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trovato. Installa Python 3.8 o superiore."
    exit 1
fi
echo -e "${GREEN}✅ Python trovato: $(python3 --version)${NC}"
echo ""

# 2. Crea virtual environment (se non esiste)
echo "🔧 Creazione virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment creato${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment già esistente, skip...${NC}"
fi
echo ""

# 3. Attiva virtual environment
echo "🔌 Attivazione virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment attivato${NC}"
echo ""

# 4. Aggiorna pip
echo "⬆️  Aggiornamento pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✅ pip aggiornato${NC}"
echo ""

# 5. Installa dipendenze
echo "📥 Installazione dipendenze..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dipendenze installate${NC}"
echo ""

# 6. Verifica file .env
echo "🔐 Verifica configurazione .env..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️  File .env non trovato. Copio da .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  IMPORTANTE: Modifica il file .env con le tue chiavi Stripe!${NC}"
    else
        echo -e "${YELLOW}⚠️  File .env non trovato. Crealo manualmente.${NC}"
    fi
else
    echo -e "${GREEN}✅ File .env trovato${NC}"
fi
echo ""

# 7. Crea migrazioni
echo "🗄️  Creazione migrazioni database..."
python3 manage.py makemigrations
echo -e "${GREEN}✅ Migrazioni create${NC}"
echo ""

# 8. Applica migrazioni
echo "📊 Applicazione migrazioni database..."
python3 manage.py migrate
echo -e "${GREEN}✅ Migrazioni applicate${NC}"
echo ""

# 9. Popola dati iniziali (prezzi)
echo "🌱 Popolamento dati iniziali (prezzi)..."
python3 manage.py seed_pricing
echo -e "${GREEN}✅ Dati iniziali popolati${NC}"
echo ""

# 10. Crea superuser (opzionale)
echo "👤 Creazione superuser per admin panel..."
echo -e "${YELLOW}Vuoi creare un superuser? (s/n)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI][iI]?|[yY][eE][sS]?)$ ]]; then
    python3 manage.py createsuperuser
    echo -e "${GREEN}✅ Superuser creato${NC}"
else
    echo -e "${YELLOW}⚠️  Superuser non creato. Puoi crearlo in seguito con: python3 manage.py createsuperuser${NC}"
fi
echo ""

echo "===================================="
echo -e "${GREEN}✅ Setup completato con successo!${NC}"
echo ""
echo "Per avviare il server, esegui:"
echo "  source venv/bin/activate"
echo "  export DJANGO_SETTINGS_MODULE=config.settings.local"
echo "  python3 manage.py runserver"
echo ""
echo "Oppure usa lo script: ./start.sh"
echo ""
