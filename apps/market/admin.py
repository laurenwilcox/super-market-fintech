from django.contrib import admin
from django.utils.html import format_html
from .models import User, Category, Product, Order, OrderItem, Transaction, OrderEvent
from core.models import AppConfiguration


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'first_name', 'balance', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_banned', 'created_at']
    search_fields = ['telegram_id', 'username', 'first_name']
    readonly_fields = ['created_at', 'updated_at', 'telegram_id']
    fieldsets = (
        ('Telegram Info', {'fields': ('telegram_id', 'username', 'first_name', 'last_name')}),
        ('Account', {'fields': ('balance', 'role', 'is_active', 'is_banned')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'is_active']
    list_filter = ['is_active', 'created_at']
    list_editable = ['position']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'quantity_available', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'external_id']
    readonly_fields = ['external_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'category', 'description')}),
        ('Pricing', {'fields': ('price', 'external_id')}),
        ('Inventory', {'fields': ('quantity_available', 'is_active')}),
        ('Delivery', {'fields': ('content_template',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'unit_price', 'subtotal']
    can_delete = False
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user_link', 'status_badge', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__telegram_id']
    readonly_fields = ['order_id', 'correlation_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {'fields': ('order_id', 'user', 'status')}),
        ('Financial', {'fields': ('total_amount', 'correlation_id')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def user_link(self, obj):
        return f"User {obj.user.telegram_id}"
    user_link.short_description = "Customer"

    def status_badge(self, obj):
        colors = {
            'created': 'gray',
            'reserved': 'blue',
            'paid': 'green',
            'delivered': 'orange',
            'completed': 'darkgreen',
            'failed': 'red',
            'cancelled': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'transaction_type', 'amount', 'reason_code', 'created_at']
    list_filter = ['transaction_type', 'reason_code', 'created_at']
    search_fields = ['transaction_id', 'user__telegram_id']
    readonly_fields = ['transaction_id', 'created_at']
    fieldsets = (
        ('Transaction', {'fields': ('transaction_id', 'order', 'user')}),
        ('Details', {'fields': ('transaction_type', 'amount', 'reason_code')}),
        ('Idempotency', {'fields': ('idempotency_key',)}),
        ('Timestamps', {'fields': ('created_at',)}),
    )


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'order', 'event_type', 'reason_code', 'created_at']
    list_filter = ['event_type', 'reason_code', 'created_at']
    search_fields = ['event_id', 'order__order_id', 'correlation_id']
    readonly_fields = ['event_id', 'correlation_id', 'created_at']
    can_delete = False


@admin.register(AppConfiguration)
class AppConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Telegram Bot', {'fields': ('bot_token', 'bot_username')}),
        ('LOLZTEAM API', {'fields': ('lolzteam_api_key', 'lolzteam_api_url')}),
        ('Redis', {'fields': ('redis_core_url', 'redis_cache_url')}),
        ('Rate Limiting', {'fields': ('rate_limit_requests', 'rate_limit_window_seconds')}),
        ('Timeouts', {'fields': ('api_timeout_seconds',)}),
        ('Payment Limits', {'fields': ('min_order_amount', 'max_order_amount')}),
        ('Bot Messages', {'fields': ('welcome_message', 'help_message')}),
    )
    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
