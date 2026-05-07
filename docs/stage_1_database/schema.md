# STAGE 1: База данных и скелет проекта

## Обзор
На этом этапе была создана фундаментальная архитектура Django-приложения, включая все основные модели данных, криптографию и систему конфигурации.

## Структура проекта

```
super_market/
├── apps/
│   └── market/
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py
│       └── admin.py
├── core/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── enums.py
│   ├── encryption.py
│   ├── fields.py
│   └── models.py
├── workers/
├── bot/
├── docs/
├── manage.py
├── requirements.txt
└── .gitignore
```

## Компоненты

### 1. Криптография (core/encryption.py)
**Keyring** — singleton-класс для управления ключами шифрования:
- Использует Fernet из криптографической библиотеки
- Поддерживает ротацию ключей (key rotation)
- Реализует MultiFernet для совместимости со старыми ключами
- Ключи загружаются из переменных окружения

### 2. Зашифрованные поля БД (core/fields.py)
- **EncryptedTextField** — TextField с шифрованием на уровне приложения
- **EncryptedCharField** — CharField с шифрованием
- Автоматическое дешифрование при чтении из БД
- Поддержка ротации ключей

### 3. Enums (core/enums.py)
Доменные перечисления для типизации:

```python
OrderStatus:
  - CREATED → RESERVED → PAID → DELIVERED → COMPLETED / FAILED
  
OrderEventType:
  - ORDER_CREATED, PAYMENT_INITIATED, PAYMENT_CONFIRMED, ITEM_DELIVERED, ...
  
ReasonCode:
  - SUCCESS, INSUFFICIENT_BALANCE, ITEM_NOT_AVAILABLE, API_ERROR, ...
  
TransactionType:
  - DEBIT, CREDIT, REFUND
  
UserRole:
  - CUSTOMER, ADMIN, MODERATOR
```

### 4. AppConfiguration (core/models.py)
**Singleton-модель** для хранения динамических настроек:
- Только один экземпляр (pk=1)
- Хранит токены бота, API-ключи, настройки Redis
- Доступна через `AppConfiguration.get_config()`
- Не может быть удалена

### 5. Основные модели БД (apps/market/models.py)

#### User (Пользователь)
- `telegram_id` — уникальный ID Telegram (indexed)
- `email`, `phone` — зашифрованные поля
- `balance` — баланс счета (DecimalField, non-negative)
- `role` — роль (CUSTOMER, ADMIN, MODERATOR)
- `is_active`, `is_banned` — флаги статуса

**Constraints:**
- Уникальность telegram_id
- Баланс ≥ 0

#### Category (Категория товара)
- `name` — уникальное имя
- `position` — позиция для отображения
- `is_active` — активность категории

#### Product (Товар)
- `external_id` — ID из LOLZTEAM API (unique, indexed)
- `category` — FK на Category (on_delete=PROTECT)
- `name`, `description` — описание
- `price` — цена (positive DecimalField)
- `quantity_available` — количество (non-negative)
- `content_template` — зашифрованный шаблон контента для доставки

**Constraints:**
- `CheckConstraint(price > 0)`
- `CheckConstraint(quantity_available >= 0)`
- Уникальность external_id

#### Order (Заказ)
- `order_id` — UUID (unique, indexed)
- `user` — FK на User (on_delete=PROTECT)
- `status` — статус заказа (FSM: CREATED → ... → COMPLETED/FAILED)
- `total_amount` — сумма заказа (positive)
- `correlation_id` — UUID для трейсирования

**Constraints:**
- `CheckConstraint(total_amount > 0)`
- Индексы: (user, created_at), status

#### OrderItem (Позиция в заказе)
- `order` — FK на Order (on_delete=PROTECT)
- `product` — FK на Product (on_delete=PROTECT)
- `quantity` — количество (positive)
- `unit_price` — цена за единицу (at purchase)
- `subtotal` — сумма позиции

**Constraints:**
- Уникальность (order, product)
- `CheckConstraint(quantity > 0)`, `CheckConstraint(unit_price > 0)`

#### Transaction (Финансовая операция)
- `transaction_id` — UUID (unique, indexed)
- `order` — FK на Order (on_delete=PROTECT)
- `user` — FK на User (on_delete=PROTECT)
- `transaction_type` — тип (DEBIT, CREDIT, REFUND)
- `amount` — сумма (positive)
- `reason_code` — код причины (SUCCESS, ERROR, etc.)
- `idempotency_key` — ключ идемпотентности (unique, indexed)

**Constraints:**
- `CheckConstraint(amount > 0)`
- Уникальность (order, transaction_type, idempotency_key) — защита от двойных платежей

#### OrderEvent (Audit-лог заказа)
- `event_id` — UUID для события (indexed)
- `order` — FK на Order (on_delete=PROTECT)
- `event_type` — тип события (ORDER_CREATED, PAYMENT_CONFIRMED, etc.)
- `reason_code` — код причины
- `correlation_id` — UUID для трейсирования
- `metadata` — JSONField для дополнительных данных

**Особенности:**
- Append-only таблица (можно только добавлять, нельзя обновлять)
- Автоматический выброс ошибки при попытке обновления

## Диаграмма связей (ER-Diagram)

```
┌─────────────┐
│   User      │
├─────────────┤
│ telegram_id │◄─┐
│ email*      │  │
│ phone*      │  │
│ balance     │  │
│ role        │  │ (on_delete=PROTECT)
│ is_active   │  │
└─────────────┘  │
       ▲         │
       │         │
       │    ┌─────────────┐
       │    │   Order     │
       │    ├─────────────┤
       └────┤ user_id     │
            │ status      │
            │ total_amt   │
            └─────────────┘
                 │
           ┌─────┴─────┐
           │           │
      ┌──────────┐  ┌──────────────┐
      │OrderItem │  │ Transaction  │
      ├──────────┤  ├──────────────┤
      │ order_id │  │ user_id      │
      │product_id│  │ order_id     │
      │quantity  │  │ amount       │
      │subtotal  │  │ idempotency_k│
      └──────────┘  └──────────────┘
           │
           │
      ┌────┴────┐
      │ Product │
      ├─────────┤
      │ name    │
      │ price   │
      │ qty_avl │
      │ content*│
      └─────────┘
           │
           │(on_delete=PROTECT)
      ┌────┴────────┐
      │  Category   │
      ├─────────────┤
      │ name        │
      │ position    │
      └─────────────┘

┌──────────────┐
│  OrderEvent  │  (Append-only)
├──────────────┤
│ order_id     │
│ event_type   │
│ reason_code  │
│ metadata     │
│ created_at   │
└──────────────┘

┌──────────────────┐
│AppConfiguration  │  (Singleton)
├──────────────────┤
│ bot_token        │
│ lolzteam_api_key │
│ redis_urls       │
│ bot_messages     │
└──────────────────┘

* = Зашифровано (EncryptedTextField)
```

## FSM Заказа

```
    ┌─────────┐
    │ CREATED │
    └────┬────┘
         │
         ▼
    ┌─────────────┐
    │  RESERVED   │ (товар зарезервирован)
    └────┬────────┘
         │
         ▼
    ┌─────────┐
    │  PAID    │ (платеж получен)
    └────┬────┘
         │
         ▼
    ┌──────────────┐
    │  DELIVERED   │ (товар отправлен/выдан)
    └────┬─────────┘
         │
         ▼
    ┌───────────┐
    │ COMPLETED │ (заказ выполнен)
    └───────────┘

Варианты ошибок:
    ┌─────────┐
    │ CREATED │
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ FAILED  │ (ошибка на любом этапе)
    └─────────┘
    
    ┌──────────────┐
    │  CANCELLED   │ (отмена пользователем)
    └──────────────┘
```

## Защита от двойных платежей (Idempotency)

**Transaction** таблица содержит:
- `idempotency_key` — уникальный ключ для каждого платежа
- Уникальность (order, transaction_type, idempotency_key)
- Гарантирует, что один платеж не будет обработан дважды

Пример:
```python
# Клиент отправляет: POST /pay?idempotency_key=uuid-123
# Если повторный запрос с тем же ключом — вернуть существующий результат
# Не будет создана новая Transaction
```

## Шифрование конфиденциальных данных

**Зашифрованные поля:**
- `User.email` — EncryptedTextField
- `User.phone` — EncryptedTextField
- `Product.content_template` — EncryptedTextField (шаблон для выдачи товара)

**Процесс:**
1. При сохранении → Keyring.encrypt(value)
2. При чтении → Keyring.decrypt(value)
3. Автоматическое дешифрование в ORM

## Миграции и инициализация

```bash
# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер
python manage.py runserver

# Доступ к администраторской панели
# http://localhost:8000/admin/
```

## Ограничения БД (Constraints)

### CheckConstraints
- `User.balance >= 0`
- `Product.price > 0`
- `Product.quantity_available >= 0`
- `Order.total_amount > 0`
- `OrderItem.quantity > 0`
- `OrderItem.unit_price > 0`
- `Transaction.amount > 0`

### UniqueConstraints
- `Product.external_id` (unique)
- `Transaction.idempotency_key` (unique)
- `(Order, Transaction.type, idempotency_key)` — защита от двойных платежей

### Foreign Keys (on_delete=PROTECT)
- `Category` → защита от удаления при наличии товаров
- `Product` → защита от удаления при наличии позиций в заказах
- `User` → защита от удаления при наличии заказов/транзакций
- `Order` → защита от удаления при наличии событий/транзакций

## Настройка переменных окружения

Файл `.env`:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here

DB_NAME=super_market
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

PRIMARY_ENCRYPTION_KEY=<Fernet-key>

REDIS_CORE_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
```

## Завершение Stage 1

✅ Директория структура создана  
✅ Django конфигурация готова  
✅ Криптография реализована (Keyring + EncryptedTextField)  
✅ Все основные модели БД созданы  
✅ Constraints и FK-защиты установлены  
✅ Admin-панель сконфигурирована  
✅ Миграции готовы к применению  

**Следующий шаг:** Stage 2 — Создание отказоустойчивого API-клиента для интеграции с LOLZTEAM Market.
