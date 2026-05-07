# -*- coding: utf-8 -*-
"""
Telegram Bot FSM States and Enums
"""

from enum import Enum


class UserState(str, Enum):
    """User states in bot FSM."""
    IDLE = "idle"
    BROWSING = "browsing"
    VIEWING_PRODUCT = "viewing_product"
    CART = "cart"
    CHECKOUT = "checkout"
    PAYMENT = "payment"
    COMPLETED = "completed"


class CartAction(str, Enum):
    """Cart manipulation actions."""
    ADD = "add"
    REMOVE = "remove"
    CLEAR = "clear"
    VIEW = "view"


class ButtonCallback(str, Enum):
    """Callback button prefixes."""
    CATEGORY = "cat"
    PRODUCT = "prod"
    CART = "cart"
    CHECKOUT = "checkout"
    CONFIRM = "confirm"
    CANCEL = "cancel"
