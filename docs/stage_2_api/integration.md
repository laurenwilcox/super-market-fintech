# STAGE 2: Отказоустойчивый API Клиент

**Дата завершения:** 2026-05-07  
**Версия:** v2.0-stage2  
**Статус:** ✅ Завершено

## Обзор

На этом этапе реализован resilient API клиент для интеграции с LOLZTEAM Market API. Включает:
- Асинхронный HTTP клиент (httpx.AsyncClient)
- Token Bucket Rate Limiter на Redis
- Exponential Backoff + Jitter для ретраев
- Маппинг HTTP статусов на доменные ReasonCodes

## Компоненты

### 1. LolzteamAPIClient (`apps/api_client/client.py`)

**Основной асинхронный клиент для работы с API LOLZTEAM**

```python
class LolzteamAPIClient:
    def __init__(api_key, api_url, timeout):
        # Инициализация с конфигурацией
        
    async def get_product(product_id) -> (success, response):
        # Получить товар по ID
        
    async def list_products(category_id) -> (success, response):
        # Получить список товаров категории
```

**Особенности:**
- ✅ Асинхронные методы (async/await)
- ✅ Встроенная поддержка rate limiting
- ✅ Автоматические ретраи с backoff
- ✅ Маппинг ошибок на ReasonCode
- ✅ Логирование всех операций

**Типичный поток:**
```
Запрос → RateLimiter.is_allowed() → httpx запрос → 
  ↓
Ответ успешен? ДА → return (True, data)
  ↓
Повторяемая ошибка (5xx, 429)? ДА → ExponentialBackoff.wait() → retry
  ↓
Постоянная ошибка (4xx)? ДА → return (False, reason_code)
```

### 2. RateLimiter (`apps/api_client/rate_limiter.py`)

**Token Bucket rate limiting на основе Redis**

```python
class RateLimiter:
    def is_allowed(max_requests, window_seconds) -> (allowed, info):
        # Проверить, разрешен ли запрос
        
    def reset():
        # Сбросить состояние
```

**Как работает:**
- Token Bucket алгоритм с Fixed-window стратегией
- На каждый окно (60 сек) выделяется max_requests токенов
- Каждый запрос расходует 1 токен
- Если токенов нет → rate limit (429)

**Пример:**
```
Window 1: [100 tokens available]
  Request 1 → tokens: 99
  Request 2 → tokens: 98
  ...
  Request 100 → tokens: 0
  Request 101 → RATE_LIMIT (reset in 45s)
```

### 3. ExponentialBackoff (`apps/api_client/backoff.py`)

**Стратегия повторных попыток с экспоненциальной задержкой**

```python
class ExponentialBackoff:
    def __init__(base_delay=1.0, max_delay=60.0, max_retries=5, jitter=True):
        # Инициализация параметров
        
    async def wait():
        # Ждать перед следующей попыткой
        
    def should_retry() -> bool:
        # Проверить, можно ли еще повторить
```

**Параметры по умолчанию:**
- base_delay: 1 сек (начальная задержка)
- max_delay: 30 сек (максимальная задержка)
- max_retries: 3 попытки
- jitter: ±10% случайный разброс

**Сроки ожидания:**
```
Попытка 1: 1.0s (+ jitter)
Попытка 2: 2.0s (+ jitter)
Попытка 3: 4.0s (+ jitter)
Попытка 4: 8.0s (+ jitter)
Попытка 5: 16.0s (+ jitter)
```

**Зачем нужен jitter?**
- Избегает "thundering herd" (все клиенты повторяют одновременно)
- Распределяет нагрузку на API более равномерно

### 4. HTTP Status Mapper (`apps/api_client/http_status_mapper.py`)

**Преобразование HTTP кодов в доменные ReasonCodes**

```python
def map_http_status_to_reason_code(status_code: int) -> ReasonCode:
    # Маппить HTTP код в ReasonCode
    
def is_retryable_status(status_code: int) -> bool:
    # Проверить, повторяемая ли ошибка
    
def is_client_error(status_code: int) -> bool:
    # Проверить, ошибка ли клиента (4xx)
```

**Маппинг:**

| HTTP код | ReasonCode | Повтор? |
|----------|------------|--------|
| 200 | SUCCESS | Нет |
| 400 | INVALID_ORDER | Нет |
| 401/403 | INVALID_USER | Нет |
| 404 | ITEM_NOT_AVAILABLE | Нет |
| 429 | RATE_LIMIT | Да |
| 500 | API_ERROR | Да |
| 502 | API_ERROR | Да |
| 503 | API_ERROR | Да |
| 504 | TIMEOUT | Да |

## Сценарии использования

### Сценарий 1: Успешный запрос

```python
client = LolzteamAPIClient()
success, response = await client.get_product('product-123')

if success:
    print(f"Товар: {response['data']}")
else:
    print(f"Ошибка: {response['reason_code']}")
```

### Сценарий 2: Rate Limit

```
API возвращает 429 → 
RateLimiter блокирует запрос → 
return (False, {'reason_code': RATE_LIMIT, 'reset_in': 45})
```

### Сценарий 3: Временная ошибка сервера

```
API возвращает 503 → 
ExponentialBackoff: 1s delay → retry →
API возвращает 503 → 
ExponentialBackoff: 2s delay → retry →
API возвращает 200 → 
return (True, {'data': ...})
```

### Сценарий 4: Network Error

```
Timeout при подключении → 
Retry #1: 1s delay →
Timeout → 
Retry #2: 2s delay →
Timeout → 
Retry #3: 4s delay →
Timeout → 
return (False, {'reason_code': TIMEOUT})
```

## Конфигурация

**AppConfiguration поля для Stage 2:**

```python
lolzteam_api_key = "your-api-key"
lolzteam_api_url = "https://api.lolzteam.net"
api_timeout_seconds = 30
rate_limit_requests = 100
rate_limit_window_seconds = 60
```

**Переменные окружения:**

```env
LOLZTEAM_API_KEY=your-api-key
LOLZTEAM_API_URL=https://api.lolzteam.net
API_TIMEOUT_SECONDS=30
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
REDIS_CORE_URL=redis://localhost:6379/0
```

## Архитектура потока запроса

```
┌─────────────┐
│   REQUEST   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ RateLimiter.is_allowed() │
│ (Token Bucket на Redis)  │
└──────┬─────┬─────────────┘
       │     │
    ДА │     │ НЕТ (429)
       │     └──────────┐
       │                │
       ▼                ▼
┌────────────────┐  ┌──────────────┐
│ httpx запрос   │  │ RATE_LIMIT   │
│ (async)        │  │ error        │
└────┬──┬────────┘  └──────────────┘
     │  │
  200│  │ 4xx/5xx
     │  │
     ▼  ▼
   ┌─────────────────────┐
   │ Retryable Status?   │
   └──┬──────────────┬───┘
      │              │
    НЕТ            ДА
      │              │
      ▼              ▼
   ┌─────┐      ┌──────────────┐
   │ OK  │      │ ExponentialB │
   │     │      │ ackoff.wait()│
   └─────┘      └──────┬───────┘
                       │
                ┌──────┴──────┐
                │ Retry left? │
                └──┬────┬─────┘
                   │    │
                  ДА    НЕТ
                   │     │
                   │     ▼
                   │  ┌────────┐
                   │  │ TIMEOUT │
                   │  └────────┘
                   │
                   ▼
            (Goto httpx запрос)
```

## Интеграция с Stage 1

**Используемые компоненты Stage 1:**
- ✅ `AppConfiguration.get_config()` для получения API ключей и настроек
- ✅ `ReasonCode` enum для консистентных кодов ошибок
- ✅ `redis-core` для rate limiting
- ✅ Логирование через Django

## Тестирование

### Unit тесты

```bash
pytest tests/test_stage2_api.py -v
```

Покрытие:
- ✅ RateLimiter: token bucket algorithm
- ✅ ExponentialBackoff: retry logic
- ✅ HTTP Status Mapper: code mapping
- ✅ API Client: error handling

### Integration тесты

```bash
pytest tests/test_stage2_integration.py -v
```

Покрытие:
- ✅ End-to-end API request flow
- ✅ Rate limiting with Redis
- ✅ Retries with backoff
- ✅ Error scenarios

### Manual testing

```python
import asyncio
from apps.api_client.client import LolzteamAPIClient

async def test():
    client = LolzteamAPIClient()
    success, response = await client.get_product('test-id')
    print(f"Success: {success}, Response: {response}")

asyncio.run(test())
```

## Метрики и мониторинг

**Логируемые события:**
```
[INFO] Successfully fetched product {product_id}
[WARNING] Retryable error {status_code}, attempt {attempt_num}
[WARNING] Timeout on attempt {attempt_num}
[WARNING] Rate limit exceeded, reset in {seconds}
[ERROR] Non-retryable error: {status_code}
[ERROR] Network error: {error_message}
[ERROR] Max retries exceeded for {resource_id}
```

**Метрики для мониторинга:**
- Total requests (по статусам)
- Rate limit hits
- Retry attempts
- Average response time
- Timeout incidents

## Готовность к Stage 3

✅ API клиент полностью готов для интеграции с Telegram ботом  
✅ Все обработки ошибок реализованы  
✅ Rate limiting защищает от блокировок  
✅ Логирование для отладки  

**Следующий этап:** Stage 3 — Создание Telegram-бота с интеграцией этого API клиента.
