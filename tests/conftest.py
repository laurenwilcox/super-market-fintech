# -*- coding: utf-8 -*-
"""
Pytest Configuration and Fixtures
Handles test environment setup, API keys, and mock services
"""

import os
import pytest
import django
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings

# Configure Django before tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


# ========== Environment Variables for Tests ==========

@pytest.fixture(scope="session")
def env_config():
    """Load environment configuration for tests."""
    return {
        # Telegram Bot
        'BOT_TOKEN': os.getenv('BOT_TOKEN', 'test-bot-token-12345:ABC-xyz'),
        'BOT_USERNAME': os.getenv('BOT_USERNAME', 'test_shop_bot'),

        # LOLZTEAM API
        'LOLZTEAM_API_KEY': os.getenv('LOLZTEAM_API_KEY', 'test-api-key-12345'),
        'LOLZTEAM_API_URL': os.getenv('LOLZTEAM_API_URL', 'https://api.lolzteam.net'),

        # Encryption
        'PRIMARY_ENCRYPTION_KEY': os.getenv(
            'PRIMARY_ENCRYPTION_KEY',
            'Drmhze6EPcv0fN_81Bj-nA' + '=' * 10  # Valid Fernet key format for tests
        ),

        # Redis
        'REDIS_CORE_URL': os.getenv('REDIS_CORE_URL', 'redis://localhost:6379/0'),
        'REDIS_CACHE_URL': os.getenv('REDIS_CACHE_URL', 'redis://localhost:6379/1'),

        # Database
        'DB_NAME': os.getenv('DB_NAME', 'super_market_test'),
        'DB_USER': os.getenv('DB_USER', 'postgres'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'DB_HOST': os.getenv('DB_HOST', 'localhost'),
        'DB_PORT': int(os.getenv('DB_PORT', 5432)),
    }


# ========== Mock API Clients ==========

@pytest.fixture
def mock_lolzteam_api():
    """Mock LOLZTEAM API client."""
    api = MagicMock()
    api.get_product = MagicMock(return_value={
        'id': 'prod_123',
        'name': 'Test Product',
        'price': 100.00,
        'description': 'Test description',
        'category_id': 'cat_1'
    })
    api.list_products = MagicMock(return_value=[
        {
            'id': f'prod_{i}',
            'name': f'Product {i}',
            'price': 100 * i,
            'category_id': f'cat_{i % 3}'
        }
        for i in range(1, 6)
    ])
    api.list_categories = MagicMock(return_value=[
        {'id': 'cat_1', 'name': 'Category 1'},
        {'id': 'cat_2', 'name': 'Category 2'},
        {'id': 'cat_3', 'name': 'Category 3'},
    ])
    return api


@pytest.fixture
def mock_telegram_client():
    """Mock Hydrogram Telegram client."""
    client = MagicMock()
    client.send_message = MagicMock()
    client.edit_message = MagicMock()
    return client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.set = MagicMock()
    redis.setex = MagicMock()
    redis.delete = MagicMock()
    redis.incr = MagicMock(return_value=1)
    redis.decr = MagicMock(return_value=0)
    return redis


@pytest.fixture
def mock_encryption_key():
    """Mock Fernet encryption key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


# ========== Database Fixtures ==========

@pytest.fixture
def test_user_data():
    """Sample user data for tests."""
    return {
        'telegram_id': 12345,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def test_product_data():
    """Sample product data for tests."""
    return {
        'id': 'prod_test_123',
        'name': 'iPhone 14 Pro',
        'price': 99990,
        'description': 'High-end smartphone',
        'category_id': 'cat_electronics',
    }


@pytest.fixture
def test_category_data():
    """Sample category data for tests."""
    return {
        'id': 'cat_electronics',
        'name': 'Электроника',
        'description': 'Electronic devices',
    }


@pytest.fixture
def test_order_data(test_user_data, test_product_data):
    """Sample order data for tests."""
    return {
        'user_id': test_user_data['telegram_id'],
        'items': [
            {
                'product_id': test_product_data['id'],
                'quantity': 1,
                'price': test_product_data['price'],
            }
        ],
        'total_amount': test_product_data['price'],
        'status': 'CREATED',
    }


# ========== HTTP Request Mocking ==========

@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for API calls."""
    return {
        'success_200': {
            'status_code': 200,
            'json': {'status': 'ok', 'data': {'id': 'test_123'}},
        },
        'created_201': {
            'status_code': 201,
            'json': {'id': 'test_456', 'created': True},
        },
        'bad_request_400': {
            'status_code': 400,
            'json': {'error': 'Invalid request'},
        },
        'unauthorized_401': {
            'status_code': 401,
            'json': {'error': 'Unauthorized'},
        },
        'not_found_404': {
            'status_code': 404,
            'json': {'error': 'Not found'},
        },
        'rate_limit_429': {
            'status_code': 429,
            'json': {'error': 'Rate limited'},
            'headers': {'Retry-After': '60'},
        },
        'server_error_500': {
            'status_code': 500,
            'json': {'error': 'Internal server error'},
        },
    }


# ========== Settings Patches ==========

@pytest.fixture
def patch_settings():
    """Context manager to patch Django settings for tests."""
    def _patch(**kwargs):
        with patch.object(settings, '_wrapped', None):
            for key, value in kwargs.items():
                setattr(settings, key, value)
    return _patch


# ========== Async Fixtures ==========

@pytest.fixture
def async_mock():
    """Create async mock for testing async functions."""
    async_func = MagicMock()
    async_func.return_value = None
    return async_func


# ========== Markers ==========

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test (requires API key)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (may take time)"
    )
    config.addinivalue_line(
        "markers", "redis_required: mark test that requires Redis"
    )
    config.addinivalue_line(
        "markers", "db_required: mark test that requires PostgreSQL"
    )


# ========== Skip Decorators ==========

skip_if_no_redis = pytest.mark.skipif(
    os.getenv('SKIP_REDIS_TESTS', 'true').lower() == 'true',
    reason="Redis not available"
)

skip_if_no_db = pytest.mark.skipif(
    os.getenv('SKIP_DB_TESTS', 'true').lower() == 'true',
    reason="Database not available"
)

skip_if_no_api_key = pytest.mark.skipif(
    os.getenv('LOLZTEAM_API_KEY', '').startswith('test-'),
    reason="Real API key required"
)
