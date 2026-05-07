# Работа с API Ключами и Секретами

## Обзор

Этот документ описывает как правильно управлять API ключами, токенами и секретными данными в проекте.

## 1. Структура хранения

### 1.1 Production (`.env` файл)

```env
# Telegram Bot
BOT_TOKEN=7123456789:ABCdefGHIjklmnoPQRstuvWXYZ
BOT_USERNAME=@shop_bot

# LOLZTEAM API
LOLZTEAM_API_KEY=your-real-api-key-here
LOLZTEAM_API_URL=https://api.lolzteam.net

# Encryption (Fernet format)
PRIMARY_ENCRYPTION_KEY=your-fernet-key-here
ENCRYPTION_KEYS=key1,key2,key3  # для ротации ключей

# Redis
REDIS_CORE_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Database
DB_NAME=super_market
DB_USER=postgres
DB_PASSWORD=postgres_password
DB_HOST=localhost
DB_PORT=5432

# Sentry
SENTRY_DSN=https://key@sentry.io/project-id
```

### 1.2 Testing (`tests/conftest.py`)

```python
@pytest.fixture(scope="session")
def env_config():
    """Load test environment configuration."""
    return {
        'BOT_TOKEN': os.getenv('BOT_TOKEN', 'test-bot-token-12345:ABC-xyz'),
        'LOLZTEAM_API_KEY': os.getenv('LOLZTEAM_API_KEY', 'test-api-key-12345'),
        'PRIMARY_ENCRYPTION_KEY': os.getenv('PRIMARY_ENCRYPTION_KEY', 'Drmhze6EPcv0fN_81Bj-nA'),
    }
```

**Ключевой момент:** Тесты используют `test-` префикс для тестовых ключей по умолчанию.

### 1.3 Git (`.gitignore`)

```gitignore
# Не коммитим секреты
.env
.env.local
*.key
*.pem
*.p12
secrets/
private/
```

## 2. Как передавать ключи в тесты

### 2.1 Через параметры fixtures

```python
def test_api_integration(env_config):
    """Test that uses API key from fixture."""
    api_key = env_config['LOLZTEAM_API_KEY']
    client = LolzteamAPIClient(api_key=api_key)
    
    # Test logic
    assert client.api_key == api_key
```

### 2.2 Через mock объекты

```python
from unittest.mock import patch

def test_with_mock_api_key():
    """Test that mocks API key."""
    mock_key = 'mock-api-key-12345'
    
    with patch('apps.api_client.client.LOLZTEAM_API_KEY', mock_key):
        client = LolzteamAPIClient()
        assert client.api_key == mock_key
```

### 2.3 Через переменные окружения в тесте

```python
import os
import pytest

def test_with_env_var():
    """Test that sets environment variable."""
    os.environ['LOLZTEAM_API_KEY'] = 'test-key-xyz'
    
    # Your test code
    from apps.api_client.client import LolzteamAPIClient
    client = LolzteamAPIClient()
    
    # Cleanup
    del os.environ['LOLZTEAM_API_KEY']
```

### 2.4 Через conftest fixtures (рекомендуется)

```python
# tests/conftest.py
@pytest.fixture
def api_client_with_key(env_config):
    """Create API client with test key."""
    from apps.api_client.client import LolzteamAPIClient
    return LolzteamAPIClient(api_key=env_config['LOLZTEAM_API_KEY'])

# tests/test_api_client.py
def test_api_call(api_client_with_key):
    """Test API call with configured client."""
    result = api_client_with_key.get_product('test_id')
    assert result is not None
```

## 3. Передача ключей в обработчики

### 3.1 Через Django settings

```python
# core/settings.py
from django.conf import settings

LOLZTEAM_API_KEY = os.getenv('LOLZTEAM_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')
```

### 3.2 Через AppConfiguration (БД)

```python
# core/models.py
class AppConfiguration(models.Model):
    """Singleton configuration model."""
    bot_token = models.CharField(max_length=500)
    bot_username = models.CharField(max_length=100)
    api_key = models.CharField(max_length=500)  # Шифруется
    
    @classmethod
    def get_config(cls):
        return cls.objects.first()
```

```python
# bot/config.py
from core.models import AppConfiguration

class BotConfig:
    @classmethod
    def get_token(cls) -> str:
        config = AppConfiguration.get_config()
        return config.bot_token
```

### 3.3 Через Keyring (для локальной разработки)

```python
import keyring

# Сохранить ключ
keyring.set_password("super_market", "lolzteam_api_key", "actual-api-key-xyz")

# Получить ключ
api_key = keyring.get_password("super_market", "lolzteam_api_key")
```

## 4. Типы ключей и их использование

### 4.1 Telegram Bot Token

```python
# ✅ Как использовать
from hydrogram import Client

async def start_bot(bot_token: str):
    app = Client("bot", bot_token=bot_token)
    await app.start()

# ✅ Как передавать в тесты
def test_bot_start(env_config):
    bot_token = env_config['BOT_TOKEN']
    assert bot_token.startswith('test-') or ':' in bot_token
```

### 4.2 LOLZTEAM API Key

```python
# ✅ Как использовать
from apps.api_client.client import LolzteamAPIClient

async def get_products(api_key: str):
    client = LolzteamAPIClient(api_key=api_key)
    return await client.list_products()

# ✅ Как передавать в тесты
@pytest.fixture
def lolzteam_client(env_config):
    return LolzteamAPIClient(
        api_key=env_config['LOLZTEAM_API_KEY'],
        api_url=env_config['LOLZTEAM_API_URL']
    )

def test_lolzteam_api(lolzteam_client):
    # Mock the actual HTTP call
    with patch('apps.api_client.client.httpx.AsyncClient') as mock_http:
        mock_http.get.return_value.json.return_value = {
            'status': 'ok',
            'data': []
        }
        # Test logic
```

### 4.3 Encryption Key (Fernet)

```python
# ✅ Как использовать
from core.encryption import Keyring

def encrypt_user_data(user_email: str, keyring: Keyring):
    encrypted = keyring.encrypt(user_email)
    return encrypted

# ✅ Как передавать в тесты
@pytest.fixture
def test_keyring(mock_encryption_key):
    from core.encryption import Keyring
    return Keyring(encryption_keys=[mock_encryption_key])

def test_encryption(test_keyring):
    encrypted = test_keyring.encrypt("user@example.com")
    assert encrypted != "user@example.com"
```

## 5. Как запускать тесты с реальными ключами

### 5.1 Локально (development)

```bash
# С тестовыми ключами (по умолчанию)
pytest tests/ -v

# С реальными ключами из .env
export LOLZTEAM_API_KEY="real-key-from-env"
pytest tests/ -v -m "not skip_real_api"

# Skip тесты которые требуют реальные ключи
pytest tests/ -v -m "not integration"
```

### 5.2 В CI/CD (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
      redis:
        image: redis:7
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        env:
          # Используем GitHub Secrets
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          LOLZTEAM_API_KEY: ${{ secrets.LOLZTEAM_API_KEY }}
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
          REDIS_CORE_URL: redis://localhost:6379/0
        run: |
          pytest tests/ -v --cov=apps --cov-report=xml
```

## 6. Передача ключей в обработчики (handlers)

### 6.1 Боту в Runtime

```python
# bot/main.py
import os
from hydrogram import Client

async def main():
    # Получить токен из .env
    bot_token = os.getenv('BOT_TOKEN')
    
    # Создать клиент
    app = Client("bot", bot_token=bot_token)
    
    # Регистрировать обработчики
    from bot.handlers import register_handlers
    register_handlers(app)
    
    # Запустить бота
    await app.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 6.2 API Client в обработчиках

```python
# bot/handlers.py
import os
from apps.api_client.client import LolzteamAPIClient

# Инициализировать при импорте
api_client = LolzteamAPIClient(
    api_key=os.getenv('LOLZTEAM_API_KEY'),
    api_url=os.getenv('LOLZTEAM_API_URL', 'https://api.lolzteam.net')
)

async def handle_catalog(client, callback_query):
    """Get categories from API."""
    categories = await api_client.list_categories()
    # ...
```

### 6.3 Тестирование обработчиков с ключами

```python
# tests/test_bot_handlers.py
from unittest.mock import patch, AsyncMock

def test_handle_catalog_with_api_key(env_config):
    """Test handler with mocked API client."""
    mock_api = AsyncMock()
    mock_api.list_categories.return_value = [
        {'id': 'cat1', 'name': 'Category 1'}
    ]
    
    with patch('bot.handlers.api_client', mock_api):
        with patch('bot.handlers.BotConfig.get_welcome_message', return_value='Welcome'):
            # Test logic
            assert mock_api.list_categories.called
```

## 7. Безопасность

### 7.1 Чек-лист

- ✅ Никогда не коммитим `.env` файл
- ✅ Используем `.gitignore` для секретов
- ✅ Тестовые ключи имеют префикс `test-`
- ✅ Реальные ключи хранятся в environment variables
- ✅ Используем `@pytest.mark.skipif` для пропуска тестов без ключей
- ✅ В CI/CD используем GitHub Secrets
- ✅ Логируем только первые 4 символа ключа
- ✅ Используем Fernet для шифрования чувствительных данных

### 7.2 Логирование ключей (НЕБЕЗОПАСНО!)

```python
# ❌ НИКОГДА так не делать
logger.info(f"API Key: {api_key}")

# ✅ Правильно
logger.info(f"API Key: {api_key[:4]}...{api_key[-4:]}")
```

## 8. Примеры команд

### 8.1 Генерация Fernet ключа

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 8.2 Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Только unit тесты
pytest tests/ -v -m "not integration"

# С покрытием
pytest tests/ --cov=apps --cov-report=html

# Конкретный тест
pytest tests/test_stage3_bot.py::TestKeyboards -v
```

### 8.3 Проверка переменных окружения

```bash
# Проверить что переменные установлены
env | grep -E "(BOT_TOKEN|LOLZTEAM|REDIS|DATABASE)"

# Вывести первые 4 символа ключей
echo "BOT_TOKEN: ${BOT_TOKEN:0:4}..."
echo "API_KEY: ${LOLZTEAM_API_KEY:0:4}..."
```

## 9. Структура conftest.py

```python
# tests/conftest.py

@pytest.fixture(scope="session")
def env_config():
    """Load environment config (одна на всю сессию тестов)."""
    return {...}

@pytest.fixture
def api_client_with_key(env_config):
    """Create API client (новый для каждого теста)."""
    return LolzteamAPIClient(api_key=env_config['LOLZTEAM_API_KEY'])

@pytest.fixture
def mock_lolzteam_api():
    """Mock API client (без реального ключа)."""
    return MagicMock()

@pytest.fixture
def mock_redis():
    """Mock Redis (без реального подключения)."""
    return MagicMock()
```

## 10. Интеграция с Stage 3 Bot

### 10.1 Как передать токен боту

```python
# bot/main.py
import os
from hydrogram import Client
from bot.handlers import register_handlers

async def start_bot():
    # Получить токен из AppConfiguration или .env
    from core.models import AppConfiguration
    config = AppConfiguration.get_config()
    bot_token = config.bot_token or os.getenv('BOT_TOKEN')
    
    # Создать клиент и запустить
    app = Client("bot", bot_token=bot_token)
    register_handlers(app)
    await app.run()
```

### 10.2 Как передать API ключ в обработчики

```python
# bot/handlers.py
import os
from apps.api_client.client import LolzteamAPIClient

# При импорте
api_client = LolzteamAPIClient(
    api_key=os.getenv('LOLZTEAM_API_KEY')
)

async def handle_catalog(client, callback_query):
    """Get catalog from API."""
    categories = await api_client.list_categories()
    # ...
```

### 10.3 Как тестировать с ключами

```python
# tests/test_stage3_bot.py
from unittest.mock import patch

def test_handle_catalog_with_api(env_config):
    """Test catalog handler with real API key mock."""
    api_key = env_config['LOLZTEAM_API_KEY']
    
    with patch('bot.handlers.api_client.api_key', api_key):
        with patch('bot.handlers.api_client.list_categories') as mock_list:
            mock_list.return_value = [{'id': 'cat1', 'name': 'Электроника'}]
            
            # Test logic
            assert mock_list.called
```

---

**Итого:**
- 📝 `.env` файл для production ключей
- 🧪 `conftest.py` для тестовых ключей
- 🔐 Никогда не коммитим секреты
- 🎯 Используем fixtures для передачи ключей в тесты
- ✅ Mock объекты для изоляции от реальных API
