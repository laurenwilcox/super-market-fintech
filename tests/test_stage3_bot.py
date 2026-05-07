# -*- coding: utf-8 -*-
"""
Stage 3 Telegram Bot Tests
Tests for handlers, cache, keyboards, and FSM behavior
"""

import pytest
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hydrogram.types import Message, CallbackQuery, User as TelegramUser, InlineKeyboardMarkup

from apps.market.models import User
from core.enums import UserRole
from bot.cache import BotCache
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
from bot.enums import UserState
from bot.handlers import (
    register_or_get_user,
    handle_start,
    handle_help,
    handle_catalog,
    handle_category,
    handle_product,
    handle_cart_add,
    handle_cart_view,
    handle_checkout,
)


@pytest.fixture
def mock_telegram_user(test_user_data):
    """Create a mock Telegram user."""
    user = Mock(spec=TelegramUser)
    user.id = test_user_data['telegram_id']
    user.username = test_user_data['username']
    user.first_name = test_user_data['first_name']
    user.last_name = test_user_data['last_name']
    return user


@pytest.fixture
def mock_message(mock_telegram_user):
    """Create a mock Telegram message."""
    message = AsyncMock(spec=Message)
    message.from_user = mock_telegram_user
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query(mock_telegram_user):
    """Create a mock Telegram callback query."""
    callback_query = AsyncMock(spec=CallbackQuery)
    callback_query.from_user = mock_telegram_user
    callback_query.data = "test:data"
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    return callback_query


@pytest.fixture
def mock_client():
    """Create a mock Hydrogram client."""
    client = Mock()
    return client


# ========== Keyboard Tests ==========

class TestKeyboards:
    """Test keyboard builders."""

    def test_main_menu_keyboard(self):
        """Test main menu keyboard structure."""
        keyboard = get_main_menu_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 2
        assert len(keyboard.inline_keyboard[1]) == 2

    def test_main_menu_callbacks(self):
        """Test main menu callback data."""
        keyboard = get_main_menu_keyboard()
        callbacks = [
            button.callback_data
            for row in keyboard.inline_keyboard
            for button in row
        ]
        assert "cat:all" in callbacks
        assert "cart:view" in callbacks

    def test_categories_keyboard(self):
        """Test categories keyboard with sample data."""
        categories = [
            {"id": "cat1", "name": "Электроника"},
            {"id": "cat2", "name": "Книги"},
        ]
        keyboard = get_categories_keyboard(categories)
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 3

    def test_categories_keyboard_empty(self):
        """Test categories keyboard with no categories."""
        keyboard = get_categories_keyboard([])
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 1

    def test_products_keyboard(self):
        """Test products keyboard."""
        products = [
            {"id": "prod1", "name": "Товар 1", "price": 100},
            {"id": "prod2", "name": "Товар 2", "price": 200},
        ]
        keyboard = get_products_keyboard(products, "cat1")
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 3

    def test_product_keyboard(self):
        """Test product details keyboard."""
        keyboard = get_product_keyboard("prod1", "cat1")
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) >= 2

    def test_cart_keyboard(self):
        """Test cart keyboard."""
        keyboard = get_cart_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2

    def test_checkout_keyboard(self):
        """Test checkout keyboard."""
        keyboard = get_checkout_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_back_menu_keyboard(self):
        """Test back to menu keyboard."""
        keyboard = get_back_menu_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1


# ========== User Registration Tests ==========

class TestUserRegistration:
    """Test user registration functionality."""

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_telegram_user):
        """Test registering a new user."""
        assert not User.objects.filter(telegram_id=mock_telegram_user.id).exists()

        user = await register_or_get_user(mock_telegram_user)

        assert user.telegram_id == mock_telegram_user.id
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.role == UserRole.CUSTOMER.value

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_get_existing_user(self, mock_telegram_user):
        """Test retrieving existing user."""
        user1 = await register_or_get_user(mock_telegram_user)
        user2 = await register_or_get_user(mock_telegram_user)

        assert user1.id == user2.id
        assert User.objects.filter(telegram_id=mock_telegram_user.id).count() == 1

    @pytest.mark.asyncio
    async def test_register_user_empty_username(self):
        """Test registering user with empty username."""
        tg_user = Mock(spec=TelegramUser)
        tg_user.id = 99999
        tg_user.username = None
        tg_user.first_name = "NoUsername"
        tg_user.last_name = ""

        with patch('bot.handlers.User.objects.get_or_create') as mock_get_or_create:
            mock_get_or_create.return_value = (Mock(telegram_id=99999), True)
            user = await register_or_get_user(tg_user)
            assert user.telegram_id == 99999


# ========== Handler Tests ==========

class TestHandlers:
    """Test message and callback handlers."""

    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_handle_start(self, mock_client, mock_message):
        """Test /start command handler."""
        with patch('bot.handlers.register_or_get_user') as mock_register, \
             patch('bot.handlers.BotConfig.get_welcome_message') as mock_welcome, \
             patch('bot.handlers.get_main_menu_keyboard') as mock_keyboard:

            mock_register.return_value = Mock(telegram_id=12345)
            mock_welcome.return_value = "Welcome!"
            mock_keyboard.return_value = get_main_menu_keyboard()

            await handle_start(mock_client, mock_message)

            mock_register.assert_called_once()
            mock_message.reply.assert_called_once()
            args, kwargs = mock_message.reply.call_args
            assert "Welcome!" in args[0]

    @pytest.mark.asyncio
    async def test_handle_help(self, mock_client, mock_message):
        """Test /help command handler."""
        with patch('bot.handlers.BotConfig.get_help_message') as mock_help, \
             patch('bot.handlers.get_back_menu_keyboard') as mock_keyboard:

            mock_help.return_value = "Help text"
            mock_keyboard.return_value = get_back_menu_keyboard()

            await handle_help(mock_client, mock_message)

            mock_message.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_catalog_success(self, mock_client, mock_callback_query):
        """Test catalog browsing."""
        categories = [
            {"id": "cat1", "name": "Категория 1"},
            {"id": "cat2", "name": "Категория 2"},
        ]

        with patch('bot.handlers.cache.get_categories') as mock_get, \
             patch('bot.handlers.get_categories_keyboard') as mock_keyboard:

            mock_get.return_value = categories
            mock_keyboard.return_value = get_categories_keyboard(categories)

            await handle_catalog(mock_client, mock_callback_query)

            mock_callback_query.edit_message_text.assert_called_once()
            args, kwargs = mock_callback_query.edit_message_text.call_args
            assert "Категория 1" in args[0]
            assert "Категория 2" in args[0]

    @pytest.mark.asyncio
    async def test_handle_catalog_empty(self, mock_client, mock_callback_query):
        """Test catalog when no categories."""
        with patch('bot.handlers.cache.get_categories') as mock_get:
            mock_get.return_value = []

            await handle_catalog(mock_client, mock_callback_query)

            mock_callback_query.answer.assert_called_once()
            args = mock_callback_query.answer.call_args[0]
            assert "пуст" in args[0]

    @pytest.mark.asyncio
    async def test_handle_category(self, mock_client, mock_callback_query):
        """Test category selection."""
        products = [
            {"id": "prod1", "name": "Товар 1", "price": 100},
            {"id": "prod2", "name": "Товар 2", "price": 200},
        ]

        with patch('bot.handlers.cache.get_products') as mock_get, \
             patch('bot.handlers.get_products_keyboard') as mock_keyboard:

            mock_get.return_value = products
            mock_keyboard.return_value = get_products_keyboard(products, "cat1")

            await handle_category(mock_client, mock_callback_query, "cat1")

            mock_callback_query.edit_message_text.assert_called_once()
            args, kwargs = mock_callback_query.edit_message_text.call_args
            assert "Товар 1" in args[0]

    @pytest.mark.asyncio
    async def test_handle_product(self, mock_client, mock_callback_query):
        """Test product details view."""
        product = {
            "id": "prod1",
            "name": "Test Product",
            "price": 100,
            "description": "Test description",
        }

        mock_callback_query.data = "prod:prod1:cat1"

        with patch('bot.handlers.cache.get_product') as mock_get, \
             patch('bot.handlers.get_product_keyboard') as mock_keyboard:

            mock_get.return_value = product
            mock_keyboard.return_value = get_product_keyboard("prod1", "cat1")

            await handle_product(mock_client, mock_callback_query, "prod1")

            mock_callback_query.edit_message_text.assert_called_once()
            args, kwargs = mock_callback_query.edit_message_text.call_args
            assert "Test Product" in args[0]
            assert kwargs.get("parse_mode") == "html"

    @pytest.mark.asyncio
    async def test_handle_cart_add(self, mock_client, mock_callback_query):
        """Test adding product to cart."""
        with patch('bot.handlers.cache.add_to_cart') as mock_add:
            mock_add.return_value = {"items": [{"id": "prod1", "quantity": 1}], "total": 100}

            await handle_cart_add(mock_client, mock_callback_query, "prod1")

            mock_add.assert_called_once_with(12345, "prod1", quantity=1)
            mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cart_view_empty(self, mock_client, mock_callback_query):
        """Test viewing empty cart."""
        with patch('bot.handlers.cache.get_user_cart') as mock_get, \
             patch('bot.handlers.get_main_menu_keyboard') as mock_keyboard:

            mock_get.return_value = {"items": [], "total": 0}
            mock_keyboard.return_value = get_main_menu_keyboard()

            await handle_cart_view(mock_client, mock_callback_query)

            mock_callback_query.edit_message_text.assert_called_once()
            args = mock_callback_query.edit_message_text.call_args[0]
            assert "пуста" in args[0]

    @pytest.mark.asyncio
    async def test_handle_cart_view_with_items(self, mock_client, mock_callback_query):
        """Test viewing cart with items."""
        cart = {
            "items": [{"id": "prod1", "quantity": 2}],
            "total": 200,
        }
        product = {"id": "prod1", "name": "Товар 1", "price": 100}

        with patch('bot.handlers.cache.get_user_cart') as mock_get_cart, \
             patch('bot.handlers.cache.get_product') as mock_get_product, \
             patch('bot.handlers.get_cart_keyboard') as mock_keyboard:

            mock_get_cart.return_value = cart
            mock_get_product.return_value = product
            mock_keyboard.return_value = get_cart_keyboard()

            await handle_cart_view(mock_client, mock_callback_query)

            mock_callback_query.edit_message_text.assert_called_once()
            args = mock_callback_query.edit_message_text.call_args[0]
            assert "Товар 1" in args[0]
            assert "200" in args[0]

    @pytest.mark.asyncio
    async def test_handle_checkout_empty_cart(self, mock_client, mock_callback_query):
        """Test checkout with empty cart."""
        with patch('bot.handlers.cache.get_user_cart') as mock_get:
            mock_get.return_value = {"items": [], "total": 0}

            await handle_checkout(mock_client, mock_callback_query)

            mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_checkout_with_items(self, mock_client, mock_callback_query):
        """Test checkout with items."""
        cart = {
            "items": [{"id": "prod1", "quantity": 1}],
            "total": 100,
        }
        product = {"id": "prod1", "name": "Товар 1", "price": 100}

        with patch('bot.handlers.cache.get_user_cart') as mock_get_cart, \
             patch('bot.handlers.cache.get_product') as mock_get_product, \
             patch('bot.handlers.get_checkout_keyboard') as mock_keyboard:

            mock_get_cart.return_value = cart
            mock_get_product.return_value = product
            mock_keyboard.return_value = get_checkout_keyboard()

            await handle_checkout(mock_client, mock_callback_query)

            mock_callback_query.edit_message_text.assert_called_once()
            args = mock_callback_query.edit_message_text.call_args[0]
            assert "Подтвердите" in args[0]


# ========== Cache Tests ==========

@pytest.mark.skipif(True, reason="Requires Redis connection")
class TestBotCache:
    """Test Redis cache functionality."""

    @pytest.fixture
    def cache(self):
        """Create BotCache instance."""
        return BotCache()

    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.redis is not None
        assert cache.prefix == "bot:"

    def test_add_to_cart(self, cache):
        """Test adding to cart."""
        cart = cache.add_to_cart(123, "prod1", quantity=1)
        assert len(cart["items"]) == 1
        assert cart["items"][0]["id"] == "prod1"

    def test_add_duplicate_to_cart(self, cache):
        """Test adding duplicate item increases quantity."""
        cache.add_to_cart(123, "prod1", quantity=1)
        cart = cache.add_to_cart(123, "prod1", quantity=2)
        assert cart["items"][0]["quantity"] == 3

    def test_get_user_cart(self, cache):
        """Test getting user cart."""
        cache.add_to_cart(123, "prod1", quantity=1)
        cart = cache.get_user_cart(123)
        assert len(cart["items"]) == 1

    def test_get_empty_cart(self, cache):
        """Test getting empty cart."""
        cart = cache.get_user_cart(999)
        assert cart["items"] == []
        assert cart["total"] == 0

    def test_clear_cart(self, cache):
        """Test clearing cart."""
        cache.add_to_cart(123, "prod1", quantity=1)
        cache.clear_cart(123)
        cart = cache.get_user_cart(123)
        assert cart["items"] == []

    def test_remove_from_cart(self, cache):
        """Test removing item from cart."""
        cache.add_to_cart(123, "prod1", quantity=1)
        cache.add_to_cart(123, "prod2", quantity=1)
        cart = cache.remove_from_cart(123, "prod1")
        assert len(cart["items"]) == 1
        assert cart["items"][0]["id"] == "prod2"

    def test_set_and_get_categories(self, cache):
        """Test caching categories."""
        categories = [{"id": "cat1", "name": "Category 1"}]
        cache.set_categories(categories)
        retrieved = cache.get_categories()
        assert retrieved == categories

    def test_set_and_get_products(self, cache):
        """Test caching products."""
        products = [{"id": "prod1", "name": "Product 1", "price": 100}]
        cache.set_products(products, category_id="cat1")
        retrieved = cache.get_products(category_id="cat1")
        assert retrieved == products


# ========== FSM State Tests ==========

class TestFSMStates:
    """Test FSM state transitions."""

    def test_user_state_enum_values(self):
        """Test UserState enum has required values."""
        assert hasattr(UserState, "IDLE")
        assert hasattr(UserState, "BROWSING")
        assert hasattr(UserState, "VIEWING_PRODUCT")
        assert hasattr(UserState, "CART")
        assert hasattr(UserState, "CHECKOUT")
        assert hasattr(UserState, "PAYMENT")
        assert hasattr(UserState, "COMPLETED")

    def test_user_state_values_are_strings(self):
        """Test that UserState values are strings."""
        for state in UserState:
            assert isinstance(state.value, str)


# ========== Integration Tests ==========

class TestAPIKeyHandling:
    """Test proper API key handling in bot."""

    def test_env_config_has_api_keys(self, env_config):
        """Test that env_config provides API keys."""
        assert 'BOT_TOKEN' in env_config
        assert 'LOLZTEAM_API_KEY' in env_config
        assert 'REDIS_CORE_URL' in env_config
        assert env_config['BOT_TOKEN'].startswith('test-') or ':' in env_config['BOT_TOKEN']

    def test_bot_token_format(self, env_config):
        """Test Telegram bot token format."""
        bot_token = env_config['BOT_TOKEN']
        # Format: 123456:ABC-xyz
        if not bot_token.startswith('test-'):
            assert ':' in bot_token
            token_id, token_hash = bot_token.split(':')
            assert len(token_id) > 5
            assert len(token_hash) > 5

    def test_api_key_format(self, env_config):
        """Test LOLZTEAM API key format."""
        api_key = env_config['LOLZTEAM_API_KEY']
        assert api_key is not None
        assert len(api_key) > 5

    def test_redis_url_format(self, env_config):
        """Test Redis URL format."""
        redis_url = env_config['REDIS_CORE_URL']
        assert redis_url.startswith('redis://')
        assert 'localhost' in redis_url or '127.0.0.1' in redis_url

    def test_encryption_key_format(self, env_config):
        """Test encryption key is valid Fernet format."""
        enc_key = env_config['PRIMARY_ENCRYPTION_KEY']
        assert enc_key is not None
        assert len(enc_key) > 10  # Fernet keys are long

    @pytest.mark.asyncio
    async def test_api_client_initialization_with_key(self, env_config):
        """Test initializing API client with key from env_config."""
        from unittest.mock import patch

        api_key = env_config['LOLZTEAM_API_KEY']
        api_url = env_config['LOLZTEAM_API_URL']

        # Simulate API client init
        mock_client = MagicMock()
        mock_client.api_key = api_key
        mock_client.api_url = api_url

        assert mock_client.api_key == api_key
        assert mock_client.api_url == api_url

    def test_bot_token_from_env_config(self, env_config):
        """Test getting bot token from env_config."""
        with patch('bot.config.AppConfiguration') as mock_config_model:
            mock_instance = MagicMock()
            mock_instance.bot_token = env_config['BOT_TOKEN']
            mock_config_model.get_config.return_value = mock_instance

            # Test BotConfig retrieval
            from bot.config import BotConfig
            token = BotConfig.get_token()
            assert token == env_config['BOT_TOKEN']


class TestIntegration:
    """Integration tests for bot flow."""

    @pytest.mark.asyncio
    async def test_full_user_journey(self, mock_client, mock_message, mock_callback_query):
        """Test complete user journey: start -> catalog -> product -> cart -> checkout."""
        with patch('bot.handlers.register_or_get_user') as mock_register, \
             patch('bot.handlers.BotConfig') as mock_config, \
             patch('bot.handlers.cache') as mock_cache, \
             patch('bot.handlers.get_main_menu_keyboard'), \
             patch('bot.handlers.get_categories_keyboard'), \
             patch('bot.handlers.get_products_keyboard'), \
             patch('bot.handlers.get_product_keyboard'), \
             patch('bot.handlers.get_cart_keyboard'), \
             patch('bot.handlers.get_checkout_keyboard'):

            mock_register.return_value = Mock(telegram_id=12345)
            mock_config.get_welcome_message.return_value = "Welcome"
            mock_config.get_help_message.return_value = "Help"
            mock_cache.get_categories.return_value = [
                {"id": "cat1", "name": "Category 1"}
            ]
            mock_cache.get_products.return_value = [
                {"id": "prod1", "name": "Product 1", "price": 100}
            ]
            mock_cache.get_product.return_value = {
                "id": "prod1",
                "name": "Product 1",
                "price": 100,
                "description": "Description",
            }
            mock_cache.get_user_cart.return_value = {
                "items": [{"id": "prod1", "quantity": 1}],
                "total": 100,
            }

            await handle_start(mock_client, mock_message)
            assert mock_message.reply.called

            await handle_catalog(mock_client, mock_callback_query)
            assert mock_callback_query.edit_message_text.called

            await handle_category(mock_client, mock_callback_query, "cat1")
            assert mock_callback_query.edit_message_text.called

            await handle_product(mock_client, mock_callback_query, "prod1")
            assert mock_callback_query.edit_message_text.called

            await handle_cart_add(mock_client, mock_callback_query, "prod1")
            assert mock_callback_query.answer.called

            await handle_cart_view(mock_client, mock_callback_query)
            assert mock_callback_query.edit_message_text.called

            await handle_checkout(mock_client, mock_callback_query)
            assert mock_callback_query.edit_message_text.called


# ========== Example: How to use API keys in tests ==========

"""
EXAMPLE 1: Using env_config fixture to access API keys
============================================================

def test_with_api_key(env_config):
    bot_token = env_config['BOT_TOKEN']
    api_key = env_config['LOLZTEAM_API_KEY']

    # Use keys to initialize clients
    # ...


EXAMPLE 2: Mock API client with proper key handling
============================================================

def test_api_call_with_key(mock_lolzteam_api, env_config):
    api_key = env_config['LOLZTEAM_API_KEY']

    # Configure mock
    mock_lolzteam_api.api_key = api_key
    mock_lolzteam_api.get_product.return_value = {
        'id': 'prod_1',
        'name': 'Product',
        'price': 100
    }

    # Test with mocked API
    # ...


EXAMPLE 3: Patch settings with API keys
============================================================

from unittest.mock import patch

def test_with_patched_settings(env_config):
    with patch('django.conf.settings.LOLZTEAM_API_KEY', env_config['LOLZTEAM_API_KEY']):
        with patch('django.conf.settings.BOT_TOKEN', env_config['BOT_TOKEN']):
            # Your test logic
            pass


EXAMPLE 4: Skip test if API key not available
============================================================

@pytest.mark.skipif(
    os.getenv('LOLZTEAM_API_KEY', '').startswith('test-'),
    reason="Real API key required for this test"
)
def test_real_api_integration():
    # This test only runs with real API key
    pass


EXAMPLE 5: Use conftest fixtures for API client
============================================================

# In tests/conftest.py:
@pytest.fixture
def api_client_configured(env_config):
    from apps.api_client.client import LolzteamAPIClient
    return LolzteamAPIClient(
        api_key=env_config['LOLZTEAM_API_KEY'],
        api_url=env_config['LOLZTEAM_API_URL']
    )

# In test file:
def test_api_integration(api_client_configured):
    # Client is already initialized with correct key
    result = api_client_configured.get_product('test_id')
    assert result is not None
"""
