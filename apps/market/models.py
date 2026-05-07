from django.db import models
from django.core.validators import MinValueValidator
from core.enums import OrderStatus, OrderEventType, ReasonCode, TransactionType, UserRole
from core.fields import EncryptedTextField
import uuid


class User(models.Model):
    """Customer/User model with encrypted sensitive data."""

    id = models.BigAutoField(primary_key=True)
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Telegram Username")
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    email = EncryptedTextField(null=True, blank=True, verbose_name="Email")
    phone = EncryptedTextField(null=True, blank=True, verbose_name="Phone")

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Account Balance"
    )

    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.name) for role in UserRole],
        default=UserRole.CUSTOMER.value,
        verbose_name="User Role"
    )

    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_banned = models.BooleanField(default=False, verbose_name="Is Banned")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"User({self.telegram_id}) - {self.first_name or 'Unknown'}"

    def can_afford(self, amount: float) -> bool:
        """Check if user has sufficient balance."""
        return self.balance >= amount


class Category(models.Model):
    """Product category."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True, verbose_name="Category Name")
    description = models.TextField(null=True, blank=True)
    position = models.IntegerField(default=0, verbose_name="Display Position")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['position']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product/Item for sale."""

    id = models.BigAutoField(primary_key=True)
    external_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="External ID (LOLZTEAM)"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="Category"
    )

    name = models.CharField(max_length=500, verbose_name="Product Name")
    description = models.TextField(null=True, blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Price"
    )

    quantity_available = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Available Quantity"
    )

    # Encrypted content delivery info
    content_template = EncryptedTextField(
        null=True,
        blank=True,
        verbose_name="Delivery Content Template"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['category', 'is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name="product_price_positive"
            ),
            models.CheckConstraint(
                check=models.Q(quantity_available__gte=0),
                name="product_quantity_non_negative"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.price} RUB)"

    def is_available(self) -> bool:
        """Check if product is available for purchase."""
        return self.is_active and self.quantity_available > 0


class Order(models.Model):
    """Customer order."""

    id = models.BigAutoField(primary_key=True)
    order_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="Order UUID"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Customer"
    )

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in OrderStatus],
        default=OrderStatus.CREATED.value,
        db_index=True,
        verbose_name="Order Status"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Total Amount"
    )

    # Correlation ID for tracing
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        verbose_name="Correlation ID"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['order_id']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_amount__gt=0),
                name="order_amount_positive"
            ),
        ]

    def __str__(self):
        return f"Order {self.order_id} - {self.user.telegram_id}"


class OrderItem(models.Model):
    """Items within an order (join table)."""

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name="Order"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Product"
    )

    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Quantity"
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Unit Price (at purchase)"
    )

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Subtotal"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        unique_together = ('order', 'product')
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="orderitem_quantity_positive"
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gt=0),
                name="orderitem_price_positive"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Transaction(models.Model):
    """Financial transaction record."""

    id = models.BigAutoField(primary_key=True)
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name="Transaction UUID"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="Order"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="User"
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=[(t_type.value, t_type.name) for t_type in TransactionType],
        verbose_name="Transaction Type"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Amount"
    )

    reason_code = models.CharField(
        max_length=50,
        choices=[(code.value, code.name) for code in ReasonCode],
        default=ReasonCode.SUCCESS.value,
        verbose_name="Reason Code"
    )

    # Idempotency key to prevent double charges
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Idempotency Key"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="transaction_amount_positive"
            ),
            models.UniqueConstraint(
                fields=['order', 'transaction_type', 'idempotency_key'],
                name="transaction_idempotency"
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.reason_code})"


class OrderEvent(models.Model):
    """Append-only audit log for order state changes."""

    id = models.BigAutoField(primary_key=True)
    event_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        verbose_name="Event UUID"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='events',
        verbose_name="Order"
    )

    event_type = models.CharField(
        max_length=50,
        choices=[(e_type.value, e_type.name) for e_type in OrderEventType],
        verbose_name="Event Type"
    )

    reason_code = models.CharField(
        max_length=50,
        choices=[(code.value, code.name) for code in ReasonCode],
        default=ReasonCode.SUCCESS.value,
        verbose_name="Reason Code"
    )

    correlation_id = models.UUIDField(
        db_index=True,
        verbose_name="Correlation ID"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Event Metadata"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Order Event"
        verbose_name_plural = "Order Events"
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['correlation_id']),
        ]
        # Append-only: prevent updates
        get_latest_by = 'created_at'

    def __str__(self):
        return f"{self.event_type} @ {self.created_at}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("OrderEvent is append-only and cannot be updated")
        super().save(*args, **kwargs)
