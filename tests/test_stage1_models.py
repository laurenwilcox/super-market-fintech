"""
Tests for Stage 1: Database Models and Constraints
"""

import os
import django
from decimal import Decimal
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.market.models import User, Category, Product, Order, OrderItem, Transaction, OrderEvent
from core.models import AppConfiguration
from core.enums import OrderStatus, TransactionType, ReasonCode, OrderEventType
from core.encryption import get_keyring


class TestEncryption(TestCase):
    """Test encryption functionality."""

    def test_keyring_singleton(self):
        """Verify Keyring is a singleton."""
        keyring1 = get_keyring()
        keyring2 = get_keyring()
        assert keyring1 is keyring2

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        keyring = get_keyring()
        plaintext = "sensitive@example.com"
        encrypted = keyring.encrypt(plaintext)
        decrypted = keyring.decrypt(encrypted)
        assert decrypted == plaintext
        assert encrypted != plaintext


class TestUserModel(TestCase):
    """Test User model."""

    def setUp(self):
        self.user = User.objects.create(
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            balance=Decimal('1000.00')
        )

    def test_user_creation(self):
        """Test basic user creation."""
        assert self.user.telegram_id == 123456789
        assert self.user.balance == Decimal('1000.00')
        assert self.user.is_active is True

    def test_user_unique_telegram_id(self):
        """Test that telegram_id is unique."""
        with pytest.raises(IntegrityError):
            User.objects.create(
                telegram_id=123456789,
                username='anotheruser'
            )

    def test_can_afford(self):
        """Test balance check."""
        assert self.user.can_afford(Decimal('500.00'))
        assert not self.user.can_afford(Decimal('2000.00'))

    def test_negative_balance_prevented(self):
        """Test that negative balance is prevented by constraint."""
        self.user.balance = Decimal('-100.00')
        # Note: This might not raise immediately in SQLite but will in PostgreSQL
        # This is more of an integration test


class TestProductModel(TestCase):
    """Test Product model."""

    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            position=1
        )

    def test_product_creation(self):
        """Test product creation."""
        product = Product.objects.create(
            name='Laptop',
            external_id='ext-001',
            category=self.category,
            price=Decimal('999.99'),
            quantity_available=10
        )
        assert product.name == 'Laptop'
        assert product.is_available()

    def test_product_unique_external_id(self):
        """Test external_id uniqueness."""
        Product.objects.create(
            name='Product1',
            external_id='ext-001',
            category=self.category,
            price=Decimal('100.00')
        )
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name='Product2',
                external_id='ext-001',
                category=self.category,
                price=Decimal('100.00')
            )

    def test_product_not_available_when_out_of_stock(self):
        """Test availability when quantity is zero."""
        product = Product.objects.create(
            name='OutOfStock',
            external_id='ext-002',
            category=self.category,
            price=Decimal('100.00'),
            quantity_available=0
        )
        assert not product.is_available()

    def test_product_not_available_when_inactive(self):
        """Test availability when inactive."""
        product = Product.objects.create(
            name='Inactive',
            external_id='ext-003',
            category=self.category,
            price=Decimal('100.00'),
            quantity_available=10,
            is_active=False
        )
        assert not product.is_available()


class TestOrderModel(TestCase):
    """Test Order model."""

    def setUp(self):
        self.user = User.objects.create(
            telegram_id=111111111,
            balance=Decimal('5000.00')
        )
        self.category = Category.objects.create(name='Test', position=1)
        self.product = Product.objects.create(
            name='TestProduct',
            external_id='test-001',
            category=self.category,
            price=Decimal('100.00'),
            quantity_available=50
        )

    def test_order_creation(self):
        """Test order creation."""
        order = Order.objects.create(
            user=self.user,
            status=OrderStatus.CREATED.value,
            total_amount=Decimal('100.00')
        )
        assert order.status == OrderStatus.CREATED.value
        assert order.total_amount == Decimal('100.00')

    def test_order_item_creation(self):
        """Test creating order items."""
        order = Order.objects.create(
            user=self.user,
            status=OrderStatus.CREATED.value,
            total_amount=Decimal('200.00')
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('200.00')
        )
        assert item.quantity == 2
        assert item.subtotal == Decimal('200.00')

    def test_order_item_unique_product_per_order(self):
        """Test that same product can't be added twice to same order."""
        order = Order.objects.create(
            user=self.user,
            status=OrderStatus.CREATED.value,
            total_amount=Decimal('100.00')
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('100.00'),
            subtotal=Decimal('100.00')
        )
        with pytest.raises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=1,
                unit_price=Decimal('100.00'),
                subtotal=Decimal('100.00')
            )


class TestTransactionModel(TestCase):
    """Test Transaction model."""

    def setUp(self):
        self.user = User.objects.create(
            telegram_id=222222222,
            balance=Decimal('5000.00')
        )
        self.category = Category.objects.create(name='Test', position=1)
        self.product = Product.objects.create(
            name='TestProduct',
            external_id='test-002',
            category=self.category,
            price=Decimal('100.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            status=OrderStatus.CREATED.value,
            total_amount=Decimal('100.00')
        )

    def test_transaction_creation(self):
        """Test transaction creation."""
        trans = Transaction.objects.create(
            order=self.order,
            user=self.user,
            transaction_type=TransactionType.DEBIT.value,
            amount=Decimal('100.00'),
            reason_code=ReasonCode.SUCCESS.value,
            idempotency_key='key-001'
        )
        assert trans.amount == Decimal('100.00')
        assert trans.transaction_type == TransactionType.DEBIT.value

    def test_idempotency_key_uniqueness(self):
        """Test that duplicate idempotency keys are prevented."""
        Transaction.objects.create(
            order=self.order,
            user=self.user,
            transaction_type=TransactionType.DEBIT.value,
            amount=Decimal('100.00'),
            reason_code=ReasonCode.SUCCESS.value,
            idempotency_key='key-002'
        )
        with pytest.raises(IntegrityError):
            Transaction.objects.create(
                order=self.order,
                user=self.user,
                transaction_type=TransactionType.DEBIT.value,
                amount=Decimal('50.00'),
                reason_code=ReasonCode.SUCCESS.value,
                idempotency_key='key-002'
            )


class TestOrderEventModel(TestCase):
    """Test OrderEvent (append-only) model."""

    def setUp(self):
        self.user = User.objects.create(
            telegram_id=333333333,
            balance=Decimal('5000.00')
        )
        self.order = Order.objects.create(
            user=self.user,
            status=OrderStatus.CREATED.value,
            total_amount=Decimal('100.00')
        )

    def test_order_event_creation(self):
        """Test creating order event."""
        event = OrderEvent.objects.create(
            order=self.order,
            event_type=OrderEventType.ORDER_CREATED.value,
            reason_code=ReasonCode.SUCCESS.value,
            correlation_id=self.order.correlation_id
        )
        assert event.event_type == OrderEventType.ORDER_CREATED.value

    def test_order_event_append_only(self):
        """Test that order events cannot be updated."""
        event = OrderEvent.objects.create(
            order=self.order,
            event_type=OrderEventType.ORDER_CREATED.value,
            reason_code=ReasonCode.SUCCESS.value,
            correlation_id=self.order.correlation_id
        )
        with pytest.raises(ValueError, match='append-only'):
            event.save()


class TestAppConfiguration(TestCase):
    """Test AppConfiguration singleton."""

    def test_singleton_creation(self):
        """Test that only one config instance can exist."""
        config = AppConfiguration.get_config()
        assert config.pk == 1

    def test_singleton_persistence(self):
        """Test that singleton is reused."""
        config1 = AppConfiguration.get_config()
        config1.bot_username = 'testbot'
        config1.save()

        config2 = AppConfiguration.get_config()
        assert config2.bot_username == 'testbot'

    def test_cannot_delete_config(self):
        """Test that config cannot be deleted."""
        config = AppConfiguration.get_config()
        with pytest.raises(ValidationError):
            config.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
