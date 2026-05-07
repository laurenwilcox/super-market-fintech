# Stage 3: Telegram Bot UI

## Описание

Stage 3 реализует полнофункциональный Telegram-бот на основе фреймворка **Hydrogram** с поддержкой:

- 📦 Каталога товаров с категориями
- 🛒 Управления корзиной (добавление, удаление, просмотр)
- ✅ Оформления заказов с подтверждением
- 💾 Кэширования товаров и корзин в Redis
- 👤 Автоматической регистрации пользователей

## Архитектура

### Основные компоненты

```
bot/
├── config.py           # Конфигурация бота (токен, сообщения)
├── enums.py            # FSM состояния и enum'ы для callback'ов
├── keyboards.py        # Построители InlineKeyboard для UI
├── cache.py            # Слой кэширования на Redis
└── handlers.py         # Обработчики сообщений и callback-запросов
```

### Зависимости

- **Hydrogram** — async фреймворк для Telegram API
- **Redis** — кэширование товаров (3600s) и корзин (86400s)
- **Django ORM** — регистрация пользователей в БД

## FSM: Состояния пользователя

Бот отслеживает поведение пользователя через FSM (Finite State Machine):

```
IDLE → BROWSING → VIEWING_PRODUCT → CART → CHECKOUT → PAYMENT → COMPLETED
```

| Состояние | Описание | Переход |
|-----------|---------|---------|
| **IDLE** | Неактивный, ожидает взаимодействия | /start → главное меню |
| **BROWSING** | Просмотр категорий и товаров | Нажатие на товар |
| **VIEWING_PRODUCT** | Открыто описание товара | Кнопка "Добавить в корзину" |
| **CART** | Просмотр содержимого корзины | Кнопка "Оформить заказ" |
| **CHECKOUT** | Подтверждение заказа | Нажатие "Подтвердить" |
| **PAYMENT** | Ожидание платежа | Система обработки (Stage 4) |
| **COMPLETED** | Заказ выполнен | Конец |

## Структура Callback Data

Все кнопки используют `callback_data` в формате `"prefix:id"` или `"prefix:action:id"`:

### Каталог и товары

```
cat:all                  # Показать все категории
cat:{category_id}        # Товары в категории
prod:{product_id}        # Детали товара
```

### Корзина

```
cart:add:{product_id}    # Добавить в корзину
cart:view                # Просмотр корзины
cart:remove:{product_id} # Удалить из корзины
cart:clear               # Очистить корзину
```

### Оформление

```
checkout:start           # Начать оформление
checkout:confirm         # Подтвердить заказ
checkout:cancel          # Отменить оформление
```

### Меню

```
menu:main                # Вернуться в главное меню
help                     # Показать справку
about                    # О боте
```

## Обработчики (Handlers)

### 1. `handle_start(client, message)`

**Триггер:** `/start` команда

**Действия:**
- Вызывает `register_or_get_user()` → создает User в БД если не существует
- Показывает приветственное сообщение из AppConfiguration
- Отправляет главное меню (InlineKeyboardMarkup)

**Главное меню:**
```
[Каталог]  [Корзина]
[Помощь]   [О боте]
```

```python
async def handle_start(client: Client, message: Message):
    user = await register_or_get_user(message.from_user)
    welcome_text = BotConfig.get_welcome_message()
    await message.reply(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
```

### 2. `handle_help(client, message)`

**Триггер:** `/help` команда или callback `help`

**Действия:**
- Показывает справочный текст из AppConfiguration
- Отправляет кнопку "Главное меню"

### 3. `handle_catalog(client, callback_query)`

**Триггер:** callback `cat:all`

**Действия:**
- Получает список категорий из Redis кэша
- Если кэш пуст → показывает ошибку "Каталог пуст"
- Формирует сообщение со списком категорий
- Возвращает KeyboardMarkup со ссылками на категории

**Кэш-ключ:** `bot:categories` (TTL: 3600 сек)

```python
async def handle_catalog(client: Client, callback_query: CallbackQuery):
    categories = cache.get_categories()
    if not categories:
        await callback_query.answer("Каталог пуст", show_alert=True)
        return
    
    text = "Выберите категорию:\n\n"
    text += "\n".join([f"• {cat['name']}" for cat in categories])
    
    await callback_query.edit_message_text(
        text,
        reply_markup=get_categories_keyboard(categories)
    )
```

### 4. `handle_category(client, callback_query, category_id)`

**Триггер:** callback `cat:{category_id}`

**Действия:**
- Получает товары категории из Redis: `bot:products:cat:{category_id}`
- Показывает список товаров с ценами
- Возвращает KeyboardMarkup с товарами

**Кэш-ключ:** `bot:products:cat:{category_id}` (TTL: 3600 сек)

### 5. `handle_product(client, callback_query, product_id)`

**Триггер:** callback `prod:{product_id}`

**Действия:**
- Получает информацию о товаре из кэша: `bot:products:all`
- Формирует HTML-сообщение с названием, ценой, описанием
- Возвращает кнопки: "Добавить в корзину", "Назад", "Меню"

**Особенности:**
- Использует `parse_mode="html"` для форматирования (`<b>`, `<i>`)
- Читает из единого кэша всех товаров для быстрого поиска

### 6. `handle_cart_add(client, callback_query, product_id)`

**Триггер:** callback `cart:add:{product_id}`

**Действия:**
- Вызывает `cache.add_to_cart(user_id, product_id, quantity=1)`
- Если товар уже в корзине → увеличивает quantity
- Отправляет notification "Товар добавлен в корзину"

**Логика:**
```python
def add_to_cart(self, user_id: int, product_id: str, quantity: int = 1) -> Dict:
    cart = self.get_user_cart(user_id)
    
    # Ищем товар в корзине
    for item in cart["items"]:
        if item["id"] == product_id:
            item["quantity"] += quantity  # Увеличиваем кол-во
            break
    else:
        # Товара нет → добавляем новый
        cart["items"].append({
            "id": product_id,
            "quantity": quantity
        })
    
    # Сохраняем в Redis на 24 часа
    self.redis.setex(f"{self.prefix}cart:{user_id}", 86400, json.dumps(cart))
    return cart
```

### 7. `handle_cart_view(client, callback_query)`

**Триггер:** callback `cart:view`

**Действия:**
- Если корзина пуста → показывает сообщение и главное меню
- Иначе:
  - Получает товары из кэша
  - Вычисляет итоговую сумму
  - Показывает: "Корзина" → список товаров → "Итого: {total}"
  - Возвращает кнопки: "Оформить заказ", "Продолжить покупки", "Очистить"

**Кэш-ключ:** `bot:cart:{user_id}` (TTL: 86400 сек)

```python
async def handle_cart_view(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cart = cache.get_user_cart(user_id)
    
    if not cart["items"]:
        await callback_query.edit_message_text(
            "Ваша корзина пуста",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    text = "Ваша корзина:\n\n"
    for item in cart["items"]:
        product = cache.get_product(item["id"])
        text += f"• {product['name']} x{item['quantity']} = {product['price'] * item['quantity']} РУБ\n"
    
    text += f"\nИтого: {cart['total']} РУБ"
    
    await callback_query.edit_message_text(
        text,
        reply_markup=get_cart_keyboard()
    )
```

### 8. `handle_checkout(client, callback_query)`

**Триггер:** callback `checkout:start`

**Действия:**
- Если корзина пуста → показывает ошибку
- Иначе:
  - Формирует сводку заказа (список товаров и сумма)
  - Показывает: "Подтвердите заказ:\n{items}\nИтого: {total}"
  - Возвращает кнопки: "Подтвердить", "Отмена"

**Примечание:** Логика создания Order в БД будет реализована в Stage 4 (Order FSM Orchestrator)

## Структура Redis Кэша

Все ключи начинаются с префикса `"bot:"` для изоляции от других сервисов:

### Категории товаров

```
bot:categories

Значение (JSON):
[
  {"id": "cat1", "name": "Электроника"},
  {"id": "cat2", "name": "Книги"}
]

TTL: 3600 сек (1 час)
```

### Товары по категориям

```
bot:products:cat:{category_id}

Значение (JSON):
[
  {"id": "prod1", "name": "iPhone 14", "price": 99990, "description": "..."},
  {"id": "prod2", "name": "Samsung S24", "price": 79990, "description": "..."}
]

TTL: 3600 сек (1 час)
```

### Все товары (быстрый поиск)

```
bot:products:all

Значение (JSON): Полный список товаров всех категорий

TTL: 3600 сек (1 час)
```

### Корзина пользователя

```
bot:cart:{user_id}

Значение (JSON):
{
  "items": [
    {"id": "prod1", "quantity": 2},
    {"id": "prod3", "quantity": 1}
  ],
  "total": 199980
}

TTL: 86400 сек (24 часа)
Примечание: Корзина живет 24 часа, даже если пользователь закроет чат
```

## Регистрация пользователя

При первом `/start` вызывается `register_or_get_user()`:

```python
async def register_or_get_user(tg_user: TelegramUser) -> User:
    user, created = User.objects.get_or_create(
        telegram_id=tg_user.id,
        defaults={
            'username': tg_user.username or '',
            'first_name': tg_user.first_name or '',
            'last_name': tg_user.last_name or '',
            'role': UserRole.CUSTOMER.value,
        }
    )
    if created:
        logger.info(f"New user registered: {tg_user.id}")
    return user
```

**Поля User:**
- `telegram_id` — уникальный ID в Telegram
- `username` — никнейм (@username) если есть
- `first_name` — имя
- `last_name` — фамилия
- `role` — роль (CUSTOMER по умолчанию)

## Клавиатуры (Keyboards)

Все клавиатуры возвращают `InlineKeyboardMarkup` — встроенные кнопки в сообщении (не занимают место в чате):

### `get_main_menu_keyboard()`

```
[Каталог]  [Корзина]
[Помощь]   [О боте]
```

### `get_categories_keyboard(categories)`

```
[Категория 1]
[Категория 2]
[Категория 3]
[Назад]
```

### `get_products_keyboard(products, category_id)`

```
[Товар 1 - 100 РУБ]
[Товар 2 - 200 РУБ]
[Назад] [Меню]
```

### `get_product_keyboard(product_id, category_id)`

```
[Добавить в корзину]
[Назад к товарам] [Меню]
```

### `get_cart_keyboard()`

```
[Оформить заказ]
[Продолжить покупки] [Очистить корзину]
```

### `get_checkout_keyboard()`

```
[Подтвердить] [Отмена]
```

### `get_back_menu_keyboard()`

```
[Главное меню]
```

## Примеры использования

### Пример 1: Начать покупку

```
Пользователь → /start

Бот:
"Добро пожаловать в наш интернет-магазин! 🛍️"

[Каталог]  [Корзина]
[Помощь]   [О боте]
```

### Пример 2: Просмотр каталога

```
Пользователь → [Каталог]

Бот:
"Выберите категорию:

• Электроника
• Книги
• Одежда"

[Электроника]
[Книги]
[Одежда]
[Назад]
```

### Пример 3: Выбор товара

```
Пользователь → [Электроника]

Бот:
"Доступные товары:

• iPhone 14 - 99990 РУБ
• Samsung S24 - 79990 РУБ"

[iPhone 14 - 99990 РУБ]
[Samsung S24 - 79990 РУБ]
[Назад] [Меню]
```

### Пример 4: Просмотр товара

```
Пользователь → [iPhone 14 - 99990 РУБ]

Бот:
"iPhone 14

Цена: 99990 РУБ

Описание: Флагманский смартфон с 
6.1-дюймовым дисплеем и процессором A17"

[Добавить в корзину]
[Назад к товарам] [Меню]
```

### Пример 5: Добавление в корзину

```
Пользователь → [Добавить в корзину]

Бот: ✓ "Товар добавлен в корзину!"
```

### Пример 6: Просмотр корзины

```
Пользователь → [Корзина] или [Оформить заказ]

Бот:
"Ваша корзина:

• iPhone 14 x1 - 99990 РУБ
• Samsung S24 x2 - 159980 РУБ

Итого: 259970 РУБ"

[Оформить заказ]
[Продолжить покупки] [Очистить корзину]
```

### Пример 7: Оформление заказа

```
Пользователь → [Оформить заказ]

Бот:
"Подтвердите заказ:

• iPhone 14 x1
• Samsung S24 x2

Итого: 259970 РУБ

Продолжить оформление?"

[Подтвердить] [Отмена]
```

## Ошибки и обработка

### Ошибка 1: Каталог пуст

```
Пользователь → [Каталог]

Бот: ⚠️ "Каталог пуст"
```

**Причина:** Redis кэш пуст (категории не загружены)

**Решение:** 
- Администратор должен загрузить категории через API
- Stage 4 будет иметь background worker для синхронизации

### Ошибка 2: Товар не найден

```
Пользователь → нажал на старый товар

Бот: ⚠️ "Товар не найден"
```

**Причина:** Товар был удален или ID больше не существует

### Ошибка 3: Корзина очищена (истекла 24 часа)

```
Пользователь вернулся через 24+ часа

Бот:
"Ваша корзина пуста"

[Главное меню]
```

**Примечание:** Redis автоматически удаляет ключ cart:{user_id} через 86400 сек

## Интеграция с другими компонентами

### Stage 1: Database Models

- **User** — регистрация пользователей по `telegram_id`
- **Category, Product** — источник данных для кэша
- **Order, OrderItem** — создание заказов при checkout (Stage 4)

### Stage 2: API Client

- Синхронизация категорий и товаров из LOLZTEAM API
- Background worker обновляет Redis кэш каждый час

### Stage 4: Order FSM + Taskiq

- Обработка callback'а `checkout:confirm`
- Создание Order в состоянии CREATED
- Запуск payment worker'а

### Stage 5: Web Admin

- Управление текстами приветствия в AppConfiguration
- Просмотр статистики по заказам из Telegram

## Тестирование

Запуск тестов Stage 3:

```bash
pytest tests/test_stage3_bot.py -v
```

**Покрытие:**
- ✅ Keyboard builders (7 тестов)
- ✅ User registration (3 теста)
- ✅ Message handlers (10+ тестов)
- ✅ Callback handlers (10+ тестов)
- ✅ FSM states (2 теста)
- ✅ Integration tests (1 full user journey)

**Пропущенные тесты:**
- ⏭️ Redis integration (требует Redis connection)

## Диаграмма потока

```
        START (/start)
            ↓
     register_or_get_user()
            ↓
     IDLE state, main menu
            ↓
      [BROWSING PATH]           [CART PATH]           [HELP PATH]
            ↓                        ↓                      ↓
      catalog (Redis)        cart:view (Redis)       help message
            ↓                        ↓                      ↓
      select category         view items              back to menu
            ↓                        ↓
      select product      [checkout or clear]
            ↓                        ↓
      product details          CHECKOUT
            ↓                        ↓
      add to cart         confirm or cancel
            ↓                        ↓
     (back to browsing)    Stage 4: Order FSM
```

## Развертывание

### Требования

```
Django 5.0+
Hydrogram 0.3.0+
Redis 7.0+
PostgreSQL 14+
```

### Переменные окружения

```env
# bot/config.py получает из AppConfiguration (БД):
BOT_TOKEN=7123456789:ABCdefGHIjklmnoPQRstuvWXYZ
BOT_USERNAME=@my_shop_bot
REDIS_CACHE_URL=redis://localhost:6379/1
```

### Запуск бота

```bash
# В отдельном процессе (после Django сервера)
python -m bot.main

# Или через Supervisor/Systemd для production
```

## Дальнейшее развитие (Stage 4-6)

- **Stage 4:** Order FSM orchestrator, платежи, Taskiq workers
- **Stage 5:** Web interface, Django Admin, CRM
- **Stage 6:** Sentry/Prometheus monitoring, Telegram notifications

---

**Версия:** 1.0  
**Дата:** 2026-05-07  
**Статус:** ✅ Завершено
