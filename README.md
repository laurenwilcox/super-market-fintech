# SuperMarket — Production-Ready Fintech Platform

**Status:** Stage 1 - Database & Foundation ✅  
**Last Updated:** 2026-05-07

## Project Overview

SuperMarket is a comprehensive fintech platform combining:
- **Telegram Bot** (Hydrogram) for direct customer interaction
- **Django Web App** for administrative management
- **LOLZTEAM API Integration** for inventory management
- **Enterprise-grade Database** with strict financial constraints
- **Asynchronous Workers** (Taskiq) for background processing
- **Real-time Monitoring** (Sentry, Prometheus)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 5+, PostgreSQL |
| Telegram Bot | Hydrogram, tgcrypto |
| Async Workers | Taskiq + Redis (2 instances) |
| Monitoring | Prometheus, Sentry |
| Encryption | Fernet (Cryptography) |
| ORM | Django ORM |
| Visualization | NodeGraphQt |

## Project Structure

```
super_market/
├── apps/
│   └── market/              # Main application models & admin
│       ├── models.py        # User, Order, Product, Transaction, etc.
│       ├── admin.py         # Django Admin configuration
│       └── ...
├── core/
│   ├── settings.py          # Django configuration
│   ├── encryption.py        # Fernet-based encryption (Keyring)
│   ├── fields.py            # EncryptedTextField, EncryptedCharField
│   ├── enums.py             # OrderStatus, ReasonCode, etc.
│   ├── models.py            # AppConfiguration (singleton)
│   └── ...
├── bot/                     # Telegram bot handlers
├── workers/                 # Taskiq background tasks
├── docs/
│   └── stage_1_database/
│       └── schema.md        # Full database documentation
├── scripts/
│   └── visualize_stage1_db.py  # NodeGraphQt visualization
├── tests/
│   └── test_stage1_models.py   # Model tests
├── manage.py                # Django management script
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

## Getting Started

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### 2. Database Setup

```bash
# Generate encryption key (if not set in .env)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser

# Create AppConfiguration singleton
python manage.py shell
>>> from core.models import AppConfiguration
>>> config = AppConfiguration.get_config()
>>> config.save()
```

### 3. Run Development Server

```bash
python manage.py runserver
# Access at http://localhost:8000/admin/
```

### 4. Visualize Database Schema

```bash
python scripts/visualize_stage1_db.py
```

This launches an interactive NodeGraphQt window showing:
- All database models and their relationships
- Field types and constraints
- Foreign key dependencies (PROTECT mode)
- Color-coded by concern (green=Users, purple=Orders, red=Transactions, lime=Events)

### 5. Run Tests

```bash
# Run all Stage 1 tests
pytest tests/test_stage1_models.py -v

# Run specific test
pytest tests/test_stage1_models.py::TestUserModel::test_user_creation -v
```

## Key Features (Stage 1)

### 🔐 Security & Encryption
- **Keyring Singleton** — Centralized encryption key management
- **Application-level Encryption** — Email, Phone, Content fields encrypted with Fernet
- **Key Rotation Support** — MultiFernet allows seamless key transitions
- **No Hardcoded Secrets** — All credentials via environment variables

### 💰 Financial Constraints
- **CheckConstraints** — Price > 0, Balance ≥ 0, Amount > 0
- **Idempotency Keys** — Prevent double-charging via unique transaction signatures
- **Foreign Key Protection** — All critical relations use `on_delete=PROTECT`
- **Append-only Audit** — OrderEvent table immutable for compliance

### 📊 Database Design
- **User** — Customers with encrypted contact info and account balance
- **Category** — Product categorization with position ordering
- **Product** — Inventory with external API sync and encrypted content
- **Order** — FSM-based order lifecycle (CREATED→PAID→DELIVERED→COMPLETED)
- **OrderItem** — Order composition with unit pricing
- **Transaction** — Financial audit trail with reason codes
- **OrderEvent** — State change history (append-only)
- **AppConfiguration** — Singleton for dynamic settings

### 🎭 FSM States

```
Order Lifecycle:
CREATED → RESERVED → PAID → DELIVERED → COMPLETED
                            ↓
                           FAILED
                           CANCELLED
```

### 🏗️ Domain-Driven Design
- **Enums** — OrderStatus, OrderEventType, ReasonCode, TransactionType, UserRole
- **Strong Typing** — Type hints throughout codebase
- **Clear Domain Model** — Business logic reflected in models

## Configuration

### Environment Variables

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_NAME=super_market
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Encryption
PRIMARY_ENCRYPTION_KEY=<Fernet-key>

# Redis
REDIS_CORE_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Telegram Bot
BOT_TOKEN=<telegram-bot-token>
BOT_USERNAME=your_bot_username

# LOLZTEAM API
LOLZTEAM_API_KEY=<api-key>
LOLZTEAM_API_URL=https://api.lolzteam.net
```

## Database Schema

For detailed ER diagram and constraints documentation, see:
- **[Stage 1 Documentation](docs/stage_1_database/schema.md)** — Full schema documentation in Russian

### Key Constraints

| Table | Constraint | Purpose |
|-------|-----------|---------|
| User | `balance >= 0` | Prevent negative balance |
| Product | `price > 0` | Valid pricing |
| Order | `total_amount > 0` | Valid order amount |
| Transaction | `(order_id, type, idempotency_key)` UNIQUE | Prevent double-charging |
| OrderEvent | Append-only (no updates) | Compliance audit trail |

## Development Workflow

### Making Changes

1. **Create migrations:**
   ```bash
   python manage.py makemigrations
   ```

2. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Write tests:**
   ```bash
   pytest tests/test_stage1_models.py -v
   ```

4. **Commit with conventional commits:**
   ```bash
   git commit -m "feat(models): add product encryption"
   ```

### Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat(scope)` — New feature
- `fix(scope)` — Bug fix
- `docs(scope)` — Documentation
- `refactor(scope)` — Code restructuring
- `test(scope)` — Tests

### Git Workflow

```bash
# Push to main
git push origin main

# Tag releases
git tag v1.0-stage1
git push origin v1.0-stage1
```

## Stages Roadmap

- ✅ **STAGE 1** — Database & Foundation (Current)
- ⏳ **STAGE 2** — API Client & Rate Limiting
- ⏳ **STAGE 3** — Telegram Bot UI
- ⏳ **STAGE 4** — Billing & Workers
- ⏳ **STAGE 5** — Web & Admin
- ⏳ **STAGE 6** — Production Ready (Sentry, Prometheus, Runbook)

## Documentation

- **[Schema Documentation](docs/stage_1_database/schema.md)** — Database design (Russian)
- **[Project Instructions](CLAUDE.md)** — Development rules and workflow
- **.env.example** — Environment configuration template

## Monitoring & Observability

**Stage 1** includes infrastructure for future monitoring:
- Sentry DSN in configuration (Stage 6)
- Prometheus endpoint preparation (Stage 6)
- Structured logging in Django

## Support & Debugging

### Common Issues

**Q: Encryption key error?**  
A: Ensure `PRIMARY_ENCRYPTION_KEY` is set in `.env`. Generate with:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Q: Migration errors?**  
A: Check database connection:
```bash
python manage.py dbshell
```

**Q: Tests failing?**  
A: Ensure PostgreSQL is running and Django can connect:
```bash
python manage.py migrate
python manage.py test
```

## License & Contributors

**Status:** Development  
**Lead Architect:** Senior Python/SRE Developer (Claude)  
**Last Updated:** 2026-05-07

---

**Next Steps:** Stage 2 will implement the resilient API client with rate limiting and retry logic for LOLZTEAM integration.
