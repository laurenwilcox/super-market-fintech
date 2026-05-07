# Локальная разработка

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/laurenwilcox/super-market-fintech.git
cd super_market
```

### 2. Создать виртуальное окружение

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Создать `.env` файл

Скопировать `.env.example` в `.env` и заполнить реальные значения:

```bash
cp .env.example .env
```

**Содержимое `.env`:**

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-for-development

# Database
DB_NAME=super_market
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Telegram Bot
BOT_TOKEN=YOUR_REAL_BOT_TOKEN_HERE
BOT_USERNAME=@your_bot_name

# LOLZTEAM API
LOLZTEAM_API_KEY=YOUR_REAL_API_KEY_HERE
LOLZTEAM_API_URL=https://api.lolzteam.net

# Redis
REDIS_CORE_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Encryption
PRIMARY_ENCRYPTION_KEY=YOUR_FERNET_KEY_HERE
```

### 5. Настроить базу данных

```bash
# Миграции
python manage.py migrate

# Создать суперпользователя (для админа)
python manage.py createsuperuser

# Загрузить данные (если есть)
python manage.py loaddata fixtures/initial_data.json
```

### 6. Запустить локальный сервер

```bash
python manage.py runserver 0.0.0.0:8000
```

Открыть http://localhost:8000

### 7. Запустить бота (в отдельном терминале)

```bash
python -m bot.main
```

### 8. Запустить тесты

```bash
pytest tests/ -v
```

---

## Генерация API ключей

### Telegram Bot Token

1. Открыть BotFather в Telegram: @BotFather
2. Отправить `/newbot`
3. Ввести имя и username бота
4. Получить token вида `123456789:ABCdefGHIjklmno...`
5. Поместить в `.env` как `BOT_TOKEN=...`

### LOLZTEAM API Key

1. Зарегистрироваться на https://api.lolzteam.net
2. Создать API ключ в личном кабинете
3. Поместить в `.env` как `LOLZTEAM_API_KEY=...`

### Fernet Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Скопировать результат в `.env` как `PRIMARY_ENCRYPTION_KEY=...`

---

## Services (Redis, PostgreSQL)

### 1. PostgreSQL

**Windows (Docker):**
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=super_market \
  -p 5432:5432 \
  postgres:14
```

**Linux/Mac (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Проверить подключение:**
```bash
psql -U postgres -d super_market -h localhost
```

### 2. Redis

**Windows (Docker):**
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7
```

**Linux/Mac (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Проверить подключение:**
```bash
redis-cli ping
# Ответ: PONG
```

---

## Структура проекта

```
super_market/
├── core/                    # Django core settings
│   ├── settings.py
│   ├── urls.py
│   ├── encryption.py        # Fernet encryption
│   ├── fields.py            # Encrypted fields
│   ├── enums.py             # Order status, etc
│   └── models.py            # AppConfiguration
│
├── apps/
│   ├── market/              # Products, Orders, Users
│   │   ├── models.py        # User, Category, Product, Order, OrderItem, etc
│   │   ├── admin.py         # Django Admin
│   │   ├── views.py         # API endpoints
│   │   └── serializers.py
│   │
│   └── api_client/          # External API integration
│       ├── client.py        # LolzteamAPIClient
│       ├── rate_limiter.py
│       ├── backoff.py
│       └── http_status_mapper.py
│
├── bot/                     # Telegram Bot
│   ├── config.py            # BotConfig
│   ├── enums.py             # FSM states
│   ├── keyboards.py         # UI builders
│   ├── cache.py             # Redis cache
│   ├── handlers.py          # Message handlers
│   └── main.py              # Bot entry point
│
├── tests/                   # Unit & integration tests
│   ├── conftest.py          # Pytest fixtures & API keys
│   ├── test_stage1_models.py
│   ├── test_stage2_api.py
│   └── test_stage3_bot.py
│
├── docs/                    # Documentation (Russian)
│   ├── KEYS_AND_SECRETS.md  # API key management
│   ├── stage_1_db/
│   ├── stage_2_api/
│   └── stage_3_bot_ui/
│
├── vizual/                  # Interactive visualizations
│   ├── stage_1/schema.html
│   ├── stage_2/api_flow.html
│   └── stage_3_bot_flow.html
│
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
└── DEVELOPMENT.md           # This file
```

---

## Типичные команды

### Django

```bash
# Создать миграцию
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Django shell
python manage.py shell

# Создать админа
python manage.py createsuperuser

# Запустить сервер
python manage.py runserver
```

### Тесты

```bash
# Все тесты
pytest tests/ -v

# Конкретный тест
pytest tests/test_stage3_bot.py::TestKeyboards -v

# С покрытием
pytest tests/ --cov=apps --cov-report=html

# Только unit (пропустить integration)
pytest tests/ -m "not integration" -v

# Только быстрые тесты
pytest tests/ -m "not slow" -v
```

### Git

```bash
# Статус
git status

# Добавить файлы
git add .

# Коммит
git commit -m "feat(feature-name): description"

# Пуш
git push origin main

# Логи
git log --oneline
```

### API тестирование

```bash
# Curl для API
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/products/

# HTTPie (более удобно)
http :8000/api/products/

# Postman
# Импортировать collection из docs/postman/
```

---

## Отладка

### Django Debug Toolbar

```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

Открыть http://localhost:8000 → видна панель внизу справа

### Django Shell

```bash
python manage.py shell

>>> from apps.market.models import User, Product
>>> users = User.objects.all()
>>> products = Product.objects.all()
>>> user = User.objects.first()
>>> print(user.telegram_id)
```

### Логирование

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Это информация")
logger.error("Это ошибка")
logger.debug("Это отладка")
```

### Redis CLI

```bash
redis-cli

# Посмотреть все ключи
KEYS *

# Посмотреть ключи бота
KEYS bot:*

# Посмотреть значение ключа
GET bot:categories

# Посмотреть TTL
TTL bot:cart:12345

# Удалить ключ
DEL bot:cart:12345

# Очистить весь Redis
FLUSHDB
```

---

## Проблемы и решения

### Проблема: "connection refused" для PostgreSQL

**Решение:**
```bash
# Проверить что PostgreSQL запущен
sudo systemctl status postgresql

# Или запустить Docker контейнер
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:14
```

### Проблема: "connection refused" для Redis

**Решение:**
```bash
# Проверить что Redis запущен
redis-cli ping

# Или запустить Docker контейнер
docker run -d -p 6379:6379 redis:7
```

### Проблема: "ModuleNotFoundError: No module named 'hydrogram'"

**Решение:**
```bash
# Переустановить зависимости
pip install -r requirements.txt

# Или отдельно
pip install hydrogram cryptg
```

### Проблема: Telegram bot не отвечает

**Решение:**
1. Проверить что BOT_TOKEN в .env правильный
2. Запустить с отладкой:
```python
# bot/main.py
logger.setLevel(logging.DEBUG)
```
3. Проверить что бот имеет доступ к интернету

### Проблема: Tests не видят .env переменные

**Решение:**
```bash
# Убедиться что .env в корне проекта
# И загружается при импорте settings

# Или явно загрузить в conftest.py
import environ
env = environ.Env()
env.read_env('.env')
```

---

## IDE Setup

### VS Code

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.python",
        "editor.formatOnSave": true
    }
}
```

### PyCharm

1. Settings → Project → Python Interpreter
2. Add Interpreter → Add Local Interpreter
3. Выбрать `.venv/bin/python`

### Расширения

- VS Code: Python, Django, REST Client
- PyCharm: Django, REST Client, .env support

---

## Production Deploy

Смотри `docs/DEPLOYMENT.md`

---

## Дополнительные ссылки

- Django docs: https://docs.djangoproject.com
- Hydrogram docs: https://docs.hydrogram.org
- Pytest docs: https://docs.pytest.org
- Redis docs: https://redis.io/docs
- PostgreSQL docs: https://www.postgresql.org/docs

---

**Вопросы?** Смотри `docs/KEYS_AND_SECRETS.md` для работы с API ключами.
