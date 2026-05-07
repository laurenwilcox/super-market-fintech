# -*- coding: utf-8 -*-
"""
Telegram Bot Keyboards and Buttons
"""

from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Каталог", callback_data="cat:all"),
        InlineKeyboardButton("Корзина", callback_data="cart:view"),
    ], [
        InlineKeyboardButton("Помощь", callback_data="help"),
        InlineKeyboardButton("О боте", callback_data="about"),
    ]])


def get_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Get categories keyboard."""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(cat['name'], callback_data=f"cat:{cat['id']}")
        ])
    buttons.append([InlineKeyboardButton("Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(buttons)


def get_products_keyboard(products: list, category_id: str) -> InlineKeyboardMarkup:
    """Get products keyboard with pagination."""
    buttons = []
    for prod in products:
        label = f"{prod['name']} - {prod['price']} РУБ"
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"prod:{prod['id']}")
        ])
    buttons.append([
        InlineKeyboardButton("Назад", callback_data=f"cat:{category_id}"),
        InlineKeyboardButton("Меню", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(buttons)


def get_product_keyboard(product_id: str, category_id: str) -> InlineKeyboardMarkup:
    """Get product details keyboard."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Добавить в корзину", callback_data=f"cart:add:{product_id}"),
    ], [
        InlineKeyboardButton("Назад к товарам", callback_data=f"cat:{category_id}"),
        InlineKeyboardButton("Меню", callback_data="menu:main"),
    ]])


def get_cart_keyboard() -> InlineKeyboardMarkup:
    """Get cart keyboard."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Оформить заказ", callback_data="checkout:start"),
    ], [
        InlineKeyboardButton("Продолжить покупки", callback_data="menu:main"),
        InlineKeyboardButton("Очистить корзину", callback_data="cart:clear"),
    ]])


def get_checkout_keyboard() -> InlineKeyboardMarkup:
    """Get checkout confirmation keyboard."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Подтвердить", callback_data="checkout:confirm"),
        InlineKeyboardButton("Отмена", callback_data="checkout:cancel"),
    ]])


def get_back_menu_keyboard() -> InlineKeyboardMarkup:
    """Get simple back to menu keyboard."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Главное меню", callback_data="menu:main"),
    ]])
