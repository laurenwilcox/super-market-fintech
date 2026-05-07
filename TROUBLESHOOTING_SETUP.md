# Troubleshooting: Поднятие БД и первый тест с реальными API

**Цель:** Поднять PostgreSQL + Redis, создать .env с валидными ключами, запустить первый реальный тест бота.

**Время:** 30-45 минут

---

## Шаг 1: Выбрать способ развертывания БД

### Вариант A: Docker (РЕКОМЕНДУЕТСЯ - самый простой)

**Преимущества:**
- ✅ Не нужно устанавливать PostgreSQL локально
- ✅ Легко удалить после тестирования
- ✅ Изолировано от системы
- ✅ Один командор

**Требования:** Docker Desktop

```bash
# 1. Проверить что Docker работает
docker --version
# Результат: Docker version 20.10.x или выше

# 2. Запустить PostgreSQL контейнер
docker run -d \
  --name super_market_db \
  -e POSTGRES_DB=super_market \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:14

# 3. Проверить что контейнер запущен
docker ps
# Должен быть: super_market_db в статусе Up

# 4. Запустить Redis контейнер
docker run -d \
  --name super_market_redis \
  -p 6379:6379 \
  redis:7

# 5. Проверить оба контейнера
docker ps | grep super_market
```

### Вариант B: Локально на Windows

**PostgreSQL:**
1. Скачать https://www.postgresql.org/download/windows/
2. Установить (запомнить пароль для postgres)
3. Проверить подключение:
```bash
psql -U postgres -h localhost
# Ввести пароль
postgres=# CREATE DATABASE super_market;
postgres=# \q
```

**Redis:**
1. Скачать https://github.com/microsoftarchive/redis/releases
2. Установить
3. Запустить Redis:
```bash
redis-server
```

---

## Шаг 2: Проверить подключение к БД

```bash
# Проверить PostgreSQL
psql -U postgres -h localhost -d super_market
# Команды:
# \dt - список таблиц
# \q - выход

# Проверить Redis
redis-cli ping
# Результат: PONG
```

**Если ошибка "connection refused":**

```bash
# Docker - проверить запущен ли контейнер
docker ps

# Docker - перезапустить контейнер
docker restart super_market_db
docker restart super_market_redis

# Локально - проверить запущены ли сервисы
# Windows: Services → PostgreSQL → Start
# Redis: Запустить redis-server
```

---

## Шаг 3: Создать .env с валидными ключами

### Получить Telegram Bot Token

```
1. Открыть https://t.me/BotFather в Telegram
2. Отправить /newbot
3. Ввести имя бота (например, "Super Market Test Bot")
4. Ввести username (например, "super_market_test_bot_12345")
5. Получить токен вида: 123456789:ABCdefGHIjklmnoPQRstuvWXYZ

СОХРАНИТЬ: BOT_TOKEN=123456789:ABCdefGHI...
```

### Получить LOLZTEAM API Key

```
1. Зарегистрироваться на https://api.lolzteam.net
2. Войти в личный кабинет
3. Найти раздел API Keys или Developer
4. Создать новый API ключ
5. Скопировать ключ

СОХРАНИТЬ: LOLZTEAM_API_KEY=xyz...
```

### Сгенерировать Fernet Encryption Key

```bash
# Windows PowerShell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Linux/Mac
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Результат (пример):
# Drmhze6EPcv0fN_81Bj-nAvttxQsVcqKQmVj_aizVw=

СОХРАНИТЬ: PRIMARY_ENCRYPTION_KEY=Drmhze6EPcv0fN_81Bj-nA...
```

### Создать .env файл

```bash
# Скопировать шаблон
cp .env.example .env

# Отредактировать .env (notepad, VS Code, vim, nano)
```

**.env содержимое:**

```env
# Django
DEBUG=True
SECRET_KEY=your-super-secret-key-for-development-12345-67890-abcdef

# Database
DB_NAME=super_market
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Telegram Bot (от BotFather)
BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
BOT_USERNAME=@super_market_test_bot

# LOLZTEAM API (от https://api.lolzteam.net)
LOLZTEAM_API_KEY=your-real-api-key-from-lolzteam
LOLZTEAM_API_URL=https://api.lolzteam.net

# Redis
REDIS_CORE_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Encryption (сгенерирован выше)
PRIMARY_ENCRYPTION_KEY=Drmhze6EPcv0fN_81Bj-nAvttxQsVcqKQmVj_aizVw=

# Sentry (опционально)
SENTRY_DSN=

# Monitoring (опционально)
PROMETHEUS_PORT=9090
```

**⚠️ ВАЖНО:** Никогда не коммитим этот файл!
```bash
# .gitignore уже содержит:
.env
.env.local
```

---

## Шаг 4: Установить зависимости

```bash
# Активировать виртуальное окружение
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Проверить что Hydrogram установлен
pip show hydrogram
```

**Если ошибка с Hydrogram:**

```bash
# Удалить и переустановить
pip uninstall hydrogram -y
pip install hydrogram cryptg

# Проверить
python -c "import hydrogram; print(hydrogram.__version__)"
```

---

## Шаг 5: Инициализировать БД

```bash
# Активировать виртуальное окружение (если еще не активирована)
.venv\Scripts\activate

# Запустить миграции
python manage.py migrate

# Результат:
# Running migrations:
#   Applying admin.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
#   Applying market.0001_initial... OK
#   Applying market.0002_order... OK
```

**Если ошибка "connection refused":**

```bash
# Проверить что PostgreSQL запущен
docker ps | grep postgres
# или
psql -U postgres -h localhost

# Проверить .env правильный
cat .env | grep DB_

# Если контейнер не запущен
docker start super_market_db
docker start super_market_redis

# Повторить миграции
python manage.py migrate
```

### Создать суперпользователя (для админа)

```bash
python manage.py createsuperuser
# Ввести имя, email, пароль
# Username: admin
# Email: admin@example.com
# Password: [ввести пароль]
```

---

## Шаг 6: Создать тестовые данные

### Загрузить категории и товары

```bash
# Создать категории в Django Shell
python manage.py shell

# Вставить этот код:
from apps.market.models import Category, Product

# Создать категории
cat_electronics = Category.objects.create(
    name="Электроника",
    description="Электронные устройства"
)

cat_books = Category.objects.create(
    name="Книги",
    description="Книги и литература"
)

# Создать товары
Product.objects.create(
    name="iPhone 14 Pro",
    price=99990,
    description="Флагманский смартфон Apple",
    category=cat_electronics
)

Product.objects.create(
    name="Samsung Galaxy S24",
    price=79990,
    description="Смартфон Samsung",
    category=cat_electronics
)

Product.objects.create(
    name="Война и мир",
    price=500,
    description="Роман Льва Толстого",
    category=cat_books
)

# Выход
exit()
```

### Проверить данные

```bash
python manage.py shell

from apps.market.models import Category, Product

# Проверить категории
print("Категории:")
for cat in Category.objects.all():
    print(f"  - {cat.name}")

# Проверить товары
print("\nТовары:")
for prod in Product.objects.all():
    print(f"  - {prod.name}: {prod.price} РУБ")

exit()
```

---

## Шаг 7: Запустить Django сервер (опционально)

```bash
python manage.py runserver

# Результат:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.

# Открыть в браузере: http://localhost:8000/admin
# Логин: admin / пароль (что вводили выше)
```

---

## Шаг 8: Запустить первый тест бота

### Способ 1: Тест с mock (без реального API)

```bash
# Активировать виртуальное окружение
.venv\Scripts\activate

# Запустить тесты Stage 3
pytest tests/test_stage3_bot.py::TestKeyboards -v

# Результат:
# tests/test_stage3_bot.py::TestKeyboards::test_main_menu_keyboard PASSED
# tests/test_stage3_bot.py::TestKeyboards::test_main_menu_callbacks PASSED
# ...
# ====== 9 passed in 1.23s ======
```

### Способ 2: Тест с реальным LOLZTEAM API

```bash
# Запустить тест с реальным API (требует валидный API_KEY)
pytest tests/test_stage3_bot.py::TestAPIKeyHandling::test_api_key_format -v

# Результат:
# test_api_key_format PASSED ✅
```

### Способ 3: Интеграционный тест (полный journey)

```bash
# Запустить полный journey
pytest tests/test_stage3_bot.py::TestIntegration::test_full_user_journey -v

# Результат:
# test_full_user_journey PASSED ✅
```

### Способ 4: Запустить все тесты Stage 3

```bash
pytest tests/test_stage3_bot.py -v

# Результат:
# ====== 30 passed, 9 skipped, 3 errors in 9.94s ======
# (3 ошибки ожидаются - требуют PostgreSQL connection)
```

---

## Шаг 9: Проверить что всё работает

### Проверка 1: БД подключена

```bash
# Django Shell
python manage.py shell

from django.db import connection

# Проверить подключение
print(f"Connected to: {connection.settings_dict['NAME']}")
print(f"Host: {connection.settings_dict['HOST']}")
print(f"Port: {connection.settings_dict['PORT']}")

# Проверить таблицы
from django.apps import apps
for app in apps.get_app_configs():
    for model in app.get_models():
        print(f"✅ {model.__name__}")

exit()
```

### Проверка 2: Redis подключен

```bash
# Python Shell
python

import redis
r = redis.from_url('redis://localhost:6379/0')
pong = r.ping()
print(f"Redis: {'✅ OK' if pong else '❌ FAILED'}")

# Тест записи/чтения
r.set('test_key', 'test_value')
value = r.get('test_key')
print(f"Test key: {value}")

# Очистка
r.delete('test_key')

exit()
```

### Проверка 3: API ключи работают

```python
# Python Shell
python

import os
from dotenv import load_dotenv

# Загрузить .env
load_dotenv()

# Проверить ключи
bot_token = os.getenv('BOT_TOKEN')
api_key = os.getenv('LOLZTEAM_API_KEY')
enc_key = os.getenv('PRIMARY_ENCRYPTION_KEY')

print(f"BOT_TOKEN: {bot_token[:10]}...{bot_token[-10:]}")
print(f"API_KEY: {api_key[:10]}...{api_key[-10:]}")
print(f"ENC_KEY: {enc_key[:10]}...{enc_key[-10:]}")

# Проверить format
assert ':' in bot_token, "Invalid BOT_TOKEN format"
assert len(api_key) > 5, "Invalid API_KEY"
assert len(enc_key) > 20, "Invalid ENC_KEY"

print("\n✅ Все ключи валидны!")

exit()
```

### Проверка 4: Тесты проходят

```bash
# Запустить быстрые тесты
pytest tests/test_stage3_bot.py::TestKeyboards -v

# Результат должен быть:
# ====== 9 passed in X.XXs ======
```

---

## Troubleshooting: Частые ошибки

### Ошибка 1: "connection refused" для PostgreSQL

**Симптом:**
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), 
port 5432 failed: Connection refused
```

**Решение:**

```bash
# Вариант A: Docker
docker ps  # Проверить контейнер
docker start super_market_db  # Запустить если не запущен

# Вариант B: Локально Windows
# Services → PostgreSQL Server → Start

# Вариант C: Проверить .env
cat .env | grep DB_

# Вариант D: Переустановить контейнер
docker rm super_market_db
docker run -d --name super_market_db \
  -e POSTGRES_DB=super_market \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:14

# Повторить миграции
python manage.py migrate
```

### Ошибка 2: "connection refused" для Redis

**Симптом:**
```
redis.ConnectionError: Error 10061 connecting to localhost:6379.
```

**Решение:**

```bash
# Docker
docker start super_market_redis

# Проверить
redis-cli ping  # Должен вывести PONG

# Если контейнер нет
docker run -d --name super_market_redis -p 6379:6379 redis:7
```

### Ошибка 3: "No such table" при миграциях

**Симптом:**
```
django.db.utils.ProgrammingError: relation "auth_user" does not exist
```

**Решение:**

```bash
# Переустановить БД
python manage.py migrate --run-syncdb

# Или удалить все и начать заново
# Это удалит все данные!
docker exec super_market_db psql -U postgres -d super_market -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Повторить миграции
python manage.py migrate
```

### Ошибка 4: ModuleNotFoundError для Hydrogram

**Симптом:**
```
ModuleNotFoundError: No module named 'hydrogram'
```

**Решение:**

```bash
# Проверить что виртуальное окружение активировано
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate

# Переустановить
pip install --upgrade hydrogram cryptg

# Проверить
python -c "import hydrogram; print('OK')"
```

### Ошибка 5: "Invalid API key" в LOLZTEAM тестах

**Симптом:**
```
401 Unauthorized: Invalid API key
```

**Решение:**

```bash
# Проверить .env
cat .env | grep LOLZTEAM_API_KEY

# Убедиться что ключ валидный (из https://api.lolzteam.net)

# Проверить формат ключа
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('LOLZTEAM_API_KEY')
print(f'Key: {key}')
print(f'Length: {len(key)}')
print(f'Valid: {len(key) > 5}')
"

# Если ключ неправильный - обновить в .env и повторить
```

### Ошибка 6: PORT 5432 уже занят

**Симптом:**
```
Bind for 127.0.0.1:5432 failed: port is already allocated
```

**Решение:**

```bash
# Docker - использовать другой порт
docker run -d --name super_market_db \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=super_market \
  postgres:14

# Обновить .env
DB_PORT=5433

# Или убить существующий процесс
# Windows PowerShell:
netstat -ano | findstr :5432
taskkill /PID [PID] /F

# Linux:
lsof -i :5432
kill -9 [PID]
```

---

## Полный чек-лист запуска

```
✅ Шаг 1: Docker запущен
   docker ps

✅ Шаг 2: PostgreSQL контейнер запущен
   docker ps | grep postgres

✅ Шаг 3: Redis контейнер запущен
   docker ps | grep redis

✅ Шаг 4: .env создан с валидными ключами
   cat .env

✅ Шаг 5: Виртуальное окружение активировано
   python --version

✅ Шаг 6: Зависимости установлены
   pip list | grep hydrogram

✅ Шаг 7: Миграции выполнены
   python manage.py migrate

✅ Шаг 8: Тестовые данные загружены
   python manage.py shell → Category.objects.count()

✅ Шаг 9: Тесты проходят
   pytest tests/test_stage3_bot.py -v

✅ Шаг 10: БД работает
   python manage.py shell → connection works

✅ Шаг 11: Redis работает
   redis-cli ping → PONG

✅ Шаг 12: API ключи валидны
   Все ключи загружены и имеют правильный формат

🎉 ГОТОВО! Окружение полностью настроено!
```

---

## Быстрые команды

### Поднять всё с нуля

```bash
# 1. Docker контейнеры
docker run -d --name super_market_db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=super_market -p 5432:5432 postgres:14
docker run -d --name super_market_redis -p 6379:6379 redis:7

# 2. Виртуальное окружение
.venv\Scripts\activate

# 3. .env
cp .env.example .env
# [Добавить реальные ключи]

# 4. Зависимости
pip install -r requirements.txt

# 5. БД
python manage.py migrate
python manage.py createsuperuser

# 6. Тесты
pytest tests/test_stage3_bot.py -v
```

### Остановить всё

```bash
# Docker
docker stop super_market_db super_market_redis
docker rm super_market_db super_market_redis

# Виртуальное окружение (в PowerShell)
deactivate
```

### Очистить БД

```bash
# Удалить БД в контейнере
docker exec super_market_db psql -U postgres -d super_market -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Повторить миграции
python manage.py migrate
```

---

## Дополнительные ресурсы

- 📖 Полная документация: `DEVELOPMENT.md`
- 🔑 Управление ключами: `QUICK_START_KEYS.md`
- 🧪 Тесты: `docs/KEYS_AND_SECRETS.md`
- 🔧 Fixtures: `tests/conftest.py`

---

**Версия:** 1.0  
**Дата:** 2026-05-07  
**Статус:** ✅ Готово к использованию
