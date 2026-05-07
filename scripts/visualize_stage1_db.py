#!/usr/bin/env python
"""
NodeGraphQt visualization script for Stage 1 database schema.
Displays ER-diagram with models and their relationships.

Usage:
    python scripts/visualize_stage1_db.py
"""

import sys
from pathlib import Path

try:
    from NodeGraphQt import NodeGraph, BaseNode
except ImportError:
    print("Error: NodeGraphQt not installed. Install with: pip install NodeGraphQt PyQt5")
    sys.exit(1)


class ModelNode(BaseNode):
    """Base node for database models."""
    NODE_NAME = 'Model'
    color = (100, 150, 200)

    def __init__(self):
        super().__init__()
        self.set_color(*self.color)


class UserNode(ModelNode):
    NODE_NAME = 'User'
    color = (60, 180, 120)

    def __init__(self):
        super().__init__()
        self.create_property('telegram_id', value='BigInt (unique)', widget_type='QLineEdit')
        self.create_property('email', value='Encrypted', widget_type='QLineEdit')
        self.create_property('phone', value='Encrypted', widget_type='QLineEdit')
        self.create_property('balance', value='Decimal (≥0)', widget_type='QLineEdit')
        self.create_property('role', value='CharField', widget_type='QLineEdit')
        self.add_output('orders')
        self.add_output('transactions')


class CategoryNode(ModelNode):
    NODE_NAME = 'Category'
    color = (200, 180, 100)

    def __init__(self):
        super().__init__()
        self.create_property('name', value='CharField (unique)', widget_type='QLineEdit')
        self.create_property('position', value='Int', widget_type='QLineEdit')
        self.add_output('products')


class ProductNode(ModelNode):
    NODE_NAME = 'Product'
    color = (200, 150, 100)

    def __init__(self):
        super().__init__()
        self.create_property('external_id', value='CharField (unique)', widget_type='QLineEdit')
        self.create_property('price', value='Decimal (>0)', widget_type='QLineEdit')
        self.create_property('quantity_available', value='Int (≥0)', widget_type='QLineEdit')
        self.create_property('content_template', value='Encrypted', widget_type='QLineEdit')
        self.add_input('category')
        self.add_output('order_items')


class OrderNode(ModelNode):
    NODE_NAME = 'Order'
    color = (180, 100, 200)

    def __init__(self):
        super().__init__()
        self.create_property('order_id', value='UUID (unique)', widget_type='QLineEdit')
        self.create_property('status', value='FSM Enum', widget_type='QLineEdit')
        self.create_property('total_amount', value='Decimal (>0)', widget_type='QLineEdit')
        self.create_property('correlation_id', value='UUID', widget_type='QLineEdit')
        self.add_input('user')
        self.add_output('items')
        self.add_output('transactions')
        self.add_output('events')


class OrderItemNode(ModelNode):
    NODE_NAME = 'OrderItem'
    color = (180, 150, 200)

    def __init__(self):
        super().__init__()
        self.create_property('quantity', value='Int (>0)', widget_type='QLineEdit')
        self.create_property('unit_price', value='Decimal (>0)', widget_type='QLineEdit')
        self.create_property('subtotal', value='Decimal (>0)', widget_type='QLineEdit')
        self.add_input('order')
        self.add_input('product')


class TransactionNode(ModelNode):
    NODE_NAME = 'Transaction'
    color = (200, 100, 100)

    def __init__(self):
        super().__init__()
        self.create_property('transaction_id', value='UUID (unique)', widget_type='QLineEdit')
        self.create_property('transaction_type', value='Enum', widget_type='QLineEdit')
        self.create_property('amount', value='Decimal (>0)', widget_type='QLineEdit')
        self.create_property('idempotency_key', value='String (unique)', widget_type='QLineEdit')
        self.create_property('reason_code', value='Enum', widget_type='QLineEdit')
        self.add_input('user')
        self.add_input('order')


class OrderEventNode(ModelNode):
    NODE_NAME = 'OrderEvent'
    color = (150, 200, 100)

    def __init__(self):
        super().__init__()
        self.create_property('event_id', value='UUID', widget_type='QLineEdit')
        self.create_property('event_type', value='Enum', widget_type='QLineEdit')
        self.create_property('reason_code', value='Enum', widget_type='QLineEdit')
        self.create_property('correlation_id', value='UUID (indexed)', widget_type='QLineEdit')
        self.create_property('metadata', value='JSON', widget_type='QLineEdit')
        self.add_input('order')


class AppConfigNode(ModelNode):
    NODE_NAME = 'AppConfiguration'
    color = (100, 100, 200)

    def __init__(self):
        super().__init__()
        self.create_property('bot_token', value='CharField', widget_type='QLineEdit')
        self.create_property('lolzteam_api_key', value='CharField', widget_type='QLineEdit')
        self.create_property('redis_core_url', value='CharField', widget_type='QLineEdit')
        self.create_property('redis_cache_url', value='CharField', widget_type='QLineEdit')


def create_graph():
    """Create and configure the node graph."""
    graph = NodeGraph()

    graph.set_title('SuperMarket Stage 1: Database Schema (ER-Diagram)')

    # Create nodes
    user_node = graph.create_node(UserNode, name='User', pos=(50, 200))
    category_node = graph.create_node(CategoryNode, name='Category', pos=(50, 50))
    product_node = graph.create_node(ProductNode, name='Product', pos=(350, 50))
    order_node = graph.create_node(OrderNode, name='Order', pos=(350, 200))
    order_item_node = graph.create_node(OrderItemNode, name='OrderItem', pos=(650, 50))
    transaction_node = graph.create_node(TransactionNode, name='Transaction', pos=(650, 300))
    order_event_node = graph.create_node(OrderEventNode, name='OrderEvent', pos=(650, 500))
    app_config_node = graph.create_node(AppConfigNode, name='AppConfiguration', pos=(350, 500))

    # Create connections (relationships)
    # Category -> Product
    category_node.set_output('products', connected_node=product_node, connected_port='category')

    # Product -> OrderItem
    product_node.set_output('order_items', connected_node=order_item_node, connected_port='product')

    # User -> Order
    user_node.set_output('orders', connected_node=order_node, connected_port='user')

    # Order -> OrderItem
    order_node.set_output('items', connected_node=order_item_node, connected_port='order')

    # User -> Transaction
    user_node.set_output('transactions', connected_node=transaction_node, connected_port='user')

    # Order -> Transaction
    order_node.set_output('transactions', connected_node=transaction_node, connected_port='order')

    # Order -> OrderEvent
    order_node.set_output('events', connected_node=order_event_node, connected_port='order')

    # Set node colors to represent different concerns
    user_node.set_color(60, 180, 120)  # Customers (green)
    order_node.set_color(180, 100, 200)  # Orders (purple)
    transaction_node.set_color(200, 100, 100)  # Transactions (red)
    order_event_node.set_color(150, 200, 100)  # Audit trail (lime)
    category_node.set_color(200, 180, 100)  # Catalog (gold)
    product_node.set_color(200, 150, 100)  # Inventory (orange)
    app_config_node.set_color(100, 100, 200)  # Configuration (blue)

    # Add annotations
    graph.add_comment(
        'Database Schema - Stage 1',
        pos=(50, 700),
        text='Green: Users | Purple: Orders | Red: Transactions | Lime: Events | Gold: Catalog'
    )
    graph.add_comment(
        'Key Features',
        pos=(350, 700),
        text='PROTECT: All foreign keys | Constraints: price>0, balance≥0, amount>0\n'
             'Encryption: Email, Phone, Content | Idempotency: Transactions | Append-only: Events'
    )

    graph.show()
    return graph


if __name__ == '__main__':
    print("Launching Stage 1 Database Visualization...")
    print("Features shown:")
    print("  - All database models and their relationships")
    print("  - Field types and constraints")
    print("  - Foreign key relationships (PROTECT)")
    print("  - Color coding: Users (green), Orders (purple), Transactions (red), Events (lime)")
    print()

    graph = create_graph()
    graph.show()
