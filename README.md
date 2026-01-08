# Aeternis Backend

Backend Django per il sistema di checkout Aeternis.

## 🚀 Quick Start

### 1. Configurazione ambiente

```bash
# Crea e attiva virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
.\venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configurazione ambiente

Copia `.env.example` in `.env` e configura le variabili:

```bash
cp .env.example .env
```

Modifica `.env` con le tue chiavi Stripe:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here

# Stripe (ottieni le chiavi da https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

### 3. Database e dati iniziali

```bash
# Crea le migrazioni
python manage.py makemigrations

# Applica le migrazioni
python manage.py migrate

# Popola i dati dei prezzi
python manage.py seed_pricing

# Crea superuser per l'admin
python manage.py createsuperuser
```

### 4. Avvia il server

```bash
python manage.py runserver
```

Il backend sarà disponibile su `http://localhost:8000`

## 📡 API Endpoints

### Pricing
- `GET /api/pricing/` - Tutti i dati prezzi (endpoint principale)
- `GET /api/pricing/plans/` - Tipi di piano
- `GET /api/pricing/materials/` - Materiali placche
- `GET /api/pricing/addons/` - Add-on disponibili
- `GET /api/pricing/discounts/` - Regole di sconto

### Orders
- `POST /api/orders/` - Crea un nuovo ordine
- `POST /api/orders/calculate/` - Calcola totale (validazione)
- `GET /api/orders/<id>/` - Dettaglio ordine
- `GET /api/orders/by-email/?email=...` - Ordini per email

### Payments
- `POST /api/payments/create-checkout-session/` - Crea sessione Stripe
- `GET /api/payments/session-status/?session_id=...` - Stato sessione
- `POST /api/payments/webhook/` - Webhook Stripe

### Admin
- `/admin/` - Pannello amministrativo Django

## 🔧 Struttura Progetto

```
aeternis_be/
├── config/              # Configurazione Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── pricing/             # App gestione prezzi
│   ├── models.py        # PlanType, StorageOption, Material, etc.
│   ├── serializers.py
│   ├── views.py
│   └── management/
│       └── commands/
│           └── seed_pricing.py
├── orders/              # App gestione ordini
│   ├── models.py        # Order, OrderProfile, OrderPlaque
│   ├── serializers.py
│   ├── services.py      # Business logic
│   └── views.py
├── payments/            # App pagamenti Stripe
│   ├── models.py        # Payment, StripeWebhookEvent
│   ├── services.py      # StripeService, WebhookHandler
│   └── views.py
├── requirements.txt
└── manage.py
```

## 💳 Configurazione Stripe

### Test Mode

1. Vai su [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
2. Copia le chiavi test (iniziano con `sk_test_` e `pk_test_`)
3. Inseriscile nel file `.env`

### Webhook (sviluppo locale)

Per testare i webhook in locale, usa [Stripe CLI](https://stripe.com/docs/stripe-cli):

```bash
# Installa Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhook events al backend locale
stripe listen --forward-to localhost:8000/api/payments/webhook/

# Copia il webhook secret che viene mostrato
# (inizia con whsec_) e aggiungilo a .env
```

### Webhook (produzione)

1. Vai su Stripe Dashboard > Developers > Webhooks
2. Aggiungi endpoint: `https://tuodominio.com/api/payments/webhook/`
3. Seleziona gli eventi:
   - `checkout.session.completed`
   - `checkout.session.expired`
   - `payment_intent.payment_failed`
4. Copia il webhook secret

## 🔐 Sicurezza

- **CORS**: Configurato per accettare richieste solo dal frontend
- **CSRF**: Webhook Stripe esente da CSRF protection
- **Rate Limiting**: 100 richieste/minuto per IP
- **Webhook Verification**: Firma Stripe verificata su ogni evento

## 📊 Admin Panel

Accedi a `/admin/` con le credenziali del superuser per:

- Gestire piani e prezzi
- Visualizzare ordini
- Monitorare pagamenti
- Consultare eventi webhook

## 🧪 Test API

```bash
# Health check
curl http://localhost:8000/health/

# Get pricing data
curl http://localhost:8000/api/pricing/

# Calculate order total
curl -X POST http://localhost:8000/api/orders/calculate/ \
  -H "Content-Type: application/json" \
  -d '{
    "profiles": [{
      "planType": "myaeternis",
      "storage": 1,
      "extensionYears": 0,
      "plaques": [{"material": "wood", "magnet": false, "engraving": false}]
    }]
  }'
```

## 🚀 Deploy

### Variabili ambiente produzione

```env
DEBUG=False
SECRET_KEY=<chiave-segreta-lunga-e-casuale>
ALLOWED_HOSTS=tuodominio.com,www.tuodominio.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=https://tuodominio.com
```

### Collectstatic

```bash
python manage.py collectstatic --noinput
```

---

Made with ❤️ for Aeternis
