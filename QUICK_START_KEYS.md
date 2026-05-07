# Быстрая справка: API ключи и тесты

## Где брать ключи?

### 1. Telegram Bot Token
- Открыть https://t.me/BotFather
- Отправить `/newbot`
- Получить токен: `123456789:ABCdefGHI...`
- Поместить в `.env`: `BOT_TOKEN=123456789:ABCdefGHI...`

### 2. LOLZTEAM API Key
- Зарегистрироваться на https://api.lolzteam.net
- Создать ключ в личном кабинете
- Поместить в `.env`: `LOLZTEAM_API_KEY=xyz...`

### 3. Fernet Encryption Key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
- Скопировать результат в `.env`: `PRIMARY_ENCRYPTION_KEY=...`

---

## Файлы с ключами

### `.env` (НИКОГДА не коммитим!)
```env
BOT_TOKEN=123456789:ABCdefGHI...
LOLZTEAM_API_KEY=your-api-key-here
PRIMARY_ENCRYPTION_KEY=Drmhze6EPcv0fN_81Bj-nA...
REDIS_CORE_URL=redis://localhost:6379/0
DB_PASSWORD=postgres_password
```

### `tests/conftest.py` (Тестовые ключи)
```python
@pytest.fixture(scope="session")
def env_config():
    return {
        'BOT_TOKEN': os.getenv('BOT_TOKEN', 'test-bot-token-12345:ABC-xyz'),
        'LOLZTEAM_API_KEY': os.getenv('LOLZTEAM_API_KEY', 'test-api-key-12345'),
        # ...
    }
```

### `.gitignore` (защита от утечек)
```
.env
.env.local
*.key
secrets/
```

---

## Как передать ключи в тесты?

### Способ 1: Через `env_config` fixture
```python
def test_with_api_key(env_config):
    bot_token = env_config['BOT_TOKEN']
    api_key = env_config['LOLZTEAM_API_KEY']
    
    # Используем ключи в тесте
    assert bot_token is not None
```

**✅ Рекомендуется для всех тестов**

### Способ 2: Через mock
```python
from unittest.mock import patch

def test_with_mock():
    with patch('bot.handlers.api_client.api_key', 'test-key'):
        # Тест с мокированным ключом
        pass
```

**✅ Используется для изоляции от реального API**

### Способ 3: Через переменные окружения
```python
import os

def test_with_env_var():
    api_key = os.getenv('LOLZTEAM_API_KEY', 'default-test-key')
    # Используем ключ
    assert api_key is not None
```

**⚠️ Менее надежно, используйте fixtures**

### Способ 4: Mock fixture
```python
def test_with_mock_api(mock_lolzteam_api):
    # mock_lolzteam_api уже инициализирован с test ключом
    result = mock_lolzteam_api.get_product('test_id')
    assert result is not None
```

**✅ Для тестирования логики без реального API**

---

## Как использовать ключи в коде?

### В handlers (bot/handlers.py)
```python
import os
from apps.api_client.client import LolzteamAPIClient

# Инициализировать клиент с ключом из .env
api_client = LolzteamAPIClient(
    api_key=os.getenv('LOLZTEAM_API_KEY')
)

async def handle_catalog(client, callback_query):
    # Использовать инициализированный клиент
    categories = await api_client.list_categories()
```

### В конфигурации (bot/config.py)
```python
from core.models import AppConfiguration

class BotConfig:
    @classmethod
    def get_token(cls) -> str:
        # Получить токен из БД
        config = AppConfiguration.get_config()
        return config.bot_token
```

### В Django settings (core/settings.py)
```python
import os

LOLZTEAM_API_KEY = os.getenv('LOLZTEAM_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')
```

---

## Как тестировать с ключами?

### Запуск тестов (по умолчанию используются тестовые ключи)
```bash
# Все тесты
pytest tests/ -v

# Только API key тесты
pytest tests/test_stage3_bot.py::TestAPIKeyHandling -v

# С покрытием
pytest tests/ --cov=apps --cov-report=html
```

### Запуск с реальными ключами (локально)
```bash
# Ключи берутся из .env файла
export LOLZTEAM_API_KEY="real-api-key-xyz"
pytest tests/ -v -m "not mock_only"
```

### Запуск в CI/CD (GitHub Actions)
```yaml
# .github/workflows/test.yml
- name: Run tests
  env:
    BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
    LOLZTEAM_API_KEY: ${{ secrets.LOLZTEAM_API_KEY }}
  run: pytest tests/ -v
```

---

## Примеры использования

### Пример 1: Тест API клиента с ключом
```python
def test_api_client(env_config):
    from apps.api_client.client import LolzteamAPIClient
    
    # Получить ключ из fixture
    api_key = env_config['LOLZTEAM_API_KEY']
    
    # Создать клиент
    client = LolzteamAPIClient(api_key=api_key)
    
    # Проверить инициализацию
    assert client.api_key == api_key
```

### Пример 2: Тест бота с токеном
```python
def test_bot_config(env_config):
    from bot.config import BotConfig
    
    bot_token = env_config['BOT_TOKEN']
    
    # Замокировать конфигурацию
    with patch('bot.config.AppConfiguration.get_config') as mock:
        mock.return_value.bot_token = bot_token
        
        # Проверить получение токена
        token = BotConfig.get_token()
        assert token == bot_token
```

### Пример 3: Интеграционный тест с реальным ключом
```python
@pytest.mark.skipif(
    os.getenv('LOLZTEAM_API_KEY', '').startswith('test-'),
    reason="Requires real API key"
)
async def test_real_api_integration():
    # Этот тест запускается только с реальным ключом
    from apps.api_client.client import LolzteamAPIClient
    
    client = LolzteamAPIClient(
        api_key=os.getenv('LOLZTEAM_API_KEY')
    )
    
    # Реальный API вызов
    products = await client.list_products()
    assert len(products) > 0
```

---

## Сценарии

### Сценарий 1: Локальная разработка
1. Копировать `.env.example` → `.env`
2. Вставить реальные ключи в `.env`
3. Тесты используют `.env` через `env_config` fixture
4. `.env` не коммитится в git

### Сценарий 2: Команда разработчиков
1. `.env.example` в гите (без реальных ключей)
2. Каждый разработчик создает свой `.env` локально
3. Ключи хранятся в 1Password/LastPass/Bitwarden
4. В CI/CD используются GitHub Secrets

### Сценарий 3: Production
1. Ключи хранятся в окружении (Docker Secrets, AWS Secrets Manager)
2. Django читает из окружения
3. Никогда не коммитятся в гит
4. Ротация ключей через переменную `ENCRYPTION_KEYS`

---

## Проверки безопасности

### ✅ Что правильно
```python
# ✅ Получать из окружения
api_key = os.getenv('LOLZTEAM_API_KEY')

# ✅ Использовать fixtures
def test_with_key(env_config):
    api_key = env_config['LOLZTEAM_API_KEY']

# ✅ Логировать только часть ключа
logger.info(f"API Key: {api_key[:4]}...{api_key[-4:]}")
```

### ❌ Что неправильно
```python
# ❌ Жестко кодировать ключи
api_key = "real-api-key-xyz"

# ❌ Коммитить .env
git add .env

# ❌ Логировать весь ключ
logger.info(f"API Key: {api_key}")

# ❌ Передавать в URL
http://api.com?key=real-key-xyz
```

---

## Дебаг

### Проверить что ключи загружены
```python
# В Django shell
python manage.py shell

>>> import os
>>> print(f"BOT_TOKEN: {os.getenv('BOT_TOKEN', 'NOT SET')}")
>>> print(f"API_KEY: {os.getenv('LOLZTEAM_API_KEY', 'NOT SET')}")
```

### Проверить format ключа
```python
bot_token = os.getenv('BOT_TOKEN')
# Должен содержать ':'
assert ':' in bot_token, "Invalid Telegram bot token format"

api_key = os.getenv('LOLZTEAM_API_KEY')
# Должен быть непустой
assert len(api_key) > 5, "API key too short"
```

### Проверить .env загруждается
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Явно загрузить
print(os.getenv('BOT_TOKEN'))
```

---

## Ссылки

- 📖 Полное руководство: `docs/KEYS_AND_SECRETS.md`
- 🚀 Локальная разработка: `DEVELOPMENT.md`
- 🧪 Примеры тестов: `tests/test_stage3_bot.py`
- 🛠️ Pytest fixtures: `tests/conftest.py`

---

**Помните:** Никогда не коммитим `.env`! Используйте `.env.example` как шаблон.
