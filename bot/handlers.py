# -*- coding: utf-8 -*-
"""
Telegram Bot Message Handlers
"""

import logging
from hydrogram import Client, filters
from hydrogram.types import Message, CallbackQuery, User as TelegramUser

from apps.market.models import User
from core.enums import UserRole
from bot.config import BotConfig
from bot.keyboards import (
    get_main_menu_keyboard,
    get_categories_keyboard,
    get_products_keyboard,
    get_product_keyboard,
    get_cart_keyboard,
    get_checkout_keyboard,
    get_back_menu_keyboard,
)
from bot.cache import BotCache
from bot.enums import UserState

logger = logging.getLogger(__name__)
cache = BotCache()


async def register_or_get_user(tg_user: TelegramUser) -> User:
    """Register user or get existing one."""
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
        logger.info(f"New user registered: {tg_user.id} (@{tg_user.username})")
    return user


async def handle_start(client: Client, message: Message):
    """Handle /start command."""
    user = await register_or_get_user(message.from_user)

    welcome_text = BotConfig.get_welcome_message()
    await message.reply(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
    logger.info(f"User {user.telegram_id} started bot")


async def handle_help(client: Client, message: Message):
    """Handle /help command."""
    help_text = BotConfig.get_help_message()
    await message.reply(
        help_text,
        reply_markup=get_back_menu_keyboard()
    )


async def handle_catalog(client: Client, callback_query: CallbackQuery):
    """Handle catalog browsing."""
    try:
        # Get categories from cache or API
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
    except Exception as e:
        logger.error(f"Error in handle_catalog: {e}")
        await callback_query.answer("Ошибка при загрузке каталога", show_alert=True)


async def handle_category(client: Client, callback_query: CallbackQuery, category_id: str):
    """Handle category selection."""
    try:
        products = cache.get_products(category_id)

        if not products:
            await callback_query.answer("Товары не найдены", show_alert=True)
            return

        text = "Доступные товары:\n\n"
        for prod in products:
            text += f"• {prod['name']} - {prod['price']} РУБ\n"

        await callback_query.edit_message_text(
            text,
            reply_markup=get_products_keyboard(products, category_id)
        )
    except Exception as e:
        logger.error(f"Error in handle_category: {e}")
        await callback_query.answer("Ошибка при загрузке товаров", show_alert=True)


async def handle_product(client: Client, callback_query: CallbackQuery, product_id: str):
    """Handle product view."""
    try:
        product = cache.get_product(product_id)

        if not product:
            await callback_query.answer("Товар не найден", show_alert=True)
            return

        text = f"<b>{product['name']}</b>\n\n"
        text += f"Цена: {product['price']} РУБ\n\n"
        text += f"Описание: {product.get('description', 'Нет описания')}"

        category_id = callback_query.data.split(":")[1] if ":" in callback_query.data else "all"

        await callback_query.edit_message_text(
            text,
            reply_markup=get_product_keyboard(product_id, category_id),
            parse_mode="html"
        )
    except Exception as e:
        logger.error(f"Error in handle_product: {e}")
        await callback_query.answer("Ошибка при загрузке товара", show_alert=True)


async def handle_cart_add(client: Client, callback_query: CallbackQuery, product_id: str):
    """Handle adding product to cart."""
    user_id = callback_query.from_user.id
    cart = cache.add_to_cart(user_id, product_id, quantity=1)

    await callback_query.answer(f"Товар добавлен в корзину!", show_alert=False)
    logger.info(f"User {user_id} added product {product_id} to cart")


async def handle_cart_view(client: Client, callback_query: CallbackQuery):
    """Handle cart view."""
    user_id = callback_query.from_user.id
    cart = cache.get_user_cart(user_id)

    if not cart["items"]:
        text = "Ваша корзина пуста"
        await callback_query.edit_message_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )
        return

    text = "Ваша корзина:\n\n"
    for item in cart["items"]:
        product = cache.get_product(item["id"])
        if product:
            text += f"• {product['name']} x{item['quantity']} - {product['price'] * item['quantity']} РУБ\n"

    text += f"\nИтого: {cart['total']} РУБ"

    await callback_query.edit_message_text(
        text,
        reply_markup=get_cart_keyboard()
    )


async def handle_checkout(client: Client, callback_query: CallbackQuery):
    """Handle checkout initiation."""
    user_id = callback_query.from_user.id
    cart = cache.get_user_cart(user_id)

    if not cart["items"]:
        await callback_query.answer("Корзина пуста", show_alert=True)
        return

    text = "Подтвердите заказ:\n\n"
    for item in cart["items"]:
        product = cache.get_product(item["id"])
        if product:
            text += f"• {product['name']} x{item['quantity']}\n"

    text += f"\nИтого: {cart['total']} РУБ\n\n"
    text += "Продолжить оформление?"

    await callback_query.edit_message_text(
        text,
        reply_markup=get_checkout_keyboard()
    )


def register_handlers(app: Client):
    """Register all bot handlers."""

    @app.on_message(filters.command("start"))
    async def on_start(client: Client, message: Message):
        await handle_start(client, message)

    @app.on_message(filters.command("help"))
    async def on_help(client: Client, message: Message):
        await handle_help(client, message)

    @app.on_callback_query()
    async def on_callback(client: Client, callback_query: CallbackQuery):
        """Handle all callback queries."""
        data = callback_query.data

        if data.startswith("cat:"):
            if data == "cat:all":
                await handle_catalog(client, callback_query)
            else:
                category_id = data.split(":")[1]
                await handle_category(client, callback_query, category_id)

        elif data.startswith("prod:"):
            product_id = data.split(":")[1]
            await handle_product(client, callback_query, product_id)

        elif data.startswith("cart:"):
            action = data.split(":")[1]
            if action == "add":
                product_id = data.split(":")[2]
                await handle_cart_add(client, callback_query, product_id)
            elif action == "view":
                await handle_cart_view(client, callback_query)
            elif action == "clear":
                cache.clear_cart(callback_query.from_user.id)
                await callback_query.answer("Корзина очищена")

        elif data.startswith("checkout:"):
            action = data.split(":")[1]
            if action == "start":
                await handle_checkout(client, callback_query)
            elif action == "confirm":
                await callback_query.answer("Заказ принят!", show_alert=True)
            elif action == "cancel":
                await callback_query.edit_message_text(
                    "Оформление отменено",
                    reply_markup=get_main_menu_keyboard()
                )

        elif data == "menu:main":
            await callback_query.edit_message_text(
                BotConfig.get_welcome_message(),
                reply_markup=get_main_menu_keyboard()
            )

        elif data == "help":
            await callback_query.edit_message_text(
                BotConfig.get_help_message(),
                reply_markup=get_back_menu_keyboard()
            )

        else:
            await callback_query.answer("Неизвестная команда")
