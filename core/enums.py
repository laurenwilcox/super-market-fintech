from enum import Enum


class OrderStatus(str, Enum):
    """Order lifecycle states (FSM: one-way progression)."""
    CREATED = "created"
    RESERVED = "reserved"
    PAID = "paid"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value == value:
                return member
        return None


class OrderEventType(str, Enum):
    """Event types for audit trail."""
    ORDER_CREATED = "order_created"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_FAILED = "payment_failed"
    ITEM_RESERVED = "item_reserved"
    ITEM_DELIVERED = "item_delivered"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"


class ReasonCode(str, Enum):
    """Domain error codes for consistent error handling."""
    SUCCESS = "success"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    ITEM_NOT_AVAILABLE = "item_not_available"
    INVALID_USER = "invalid_user"
    INVALID_ORDER = "invalid_order"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    DUPLICATE_REQUEST = "duplicate_request"
    UNKNOWN_ERROR = "unknown_error"


class TransactionType(str, Enum):
    """Transaction types for financial audit."""
    DEBIT = "debit"
    CREDIT = "credit"
    REFUND = "refund"


class UserRole(str, Enum):
    """User roles in the system."""
    CUSTOMER = "customer"
    ADMIN = "admin"
    MODERATOR = "moderator"
