# -*- coding: utf-8 -*-
"""
Redis Cache Layer for Bot
Handles product showcase and shopping cart
"""

import json
import redis
from typing import Optional, Dict, List
from django.conf import settings


class BotCache:
    """Cache manager for bot using Redis."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)
        self.prefix = "bot:"

    def get_user_cart(self, user_id: int) -> Dict:
        """Get user's shopping cart."""
        key = f"{self.prefix}cart:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else {"items": [], "total": 0}

    def add_to_cart(self, user_id: int, product_id: str, quantity: int = 1) -> Dict:
        """Add product to cart."""
        cart = self.get_user_cart(user_id)

        # Check if product already in cart
        for item in cart["items"]:
            if item["id"] == product_id:
                item["quantity"] += quantity
                break
        else:
            cart["items"].append({
                "id": product_id,
                "quantity": quantity
            })

        key = f"{self.prefix}cart:{user_id}"
        self.redis.setex(key, 86400, json.dumps(cart))  # 24 hours
        return cart

    def remove_from_cart(self, user_id: int, product_id: str) -> Dict:
        """Remove product from cart."""
        cart = self.get_user_cart(user_id)
        cart["items"] = [item for item in cart["items"] if item["id"] != product_id]

        key = f"{self.prefix}cart:{user_id}"
        self.redis.setex(key, 86400, json.dumps(cart))
        return cart

    def clear_cart(self, user_id: int):
        """Clear user's cart."""
        key = f"{self.prefix}cart:{user_id}"
        self.redis.delete(key)

    def get_categories(self) -> List[Dict]:
        """Get product categories from cache."""
        key = f"{self.prefix}categories"
        data = self.redis.get(key)
        return json.loads(data) if data else []

    def set_categories(self, categories: List[Dict], ttl: int = 3600):
        """Cache product categories."""
        key = f"{self.prefix}categories"
        self.redis.setex(key, ttl, json.dumps(categories))

    def get_products(self, category_id: Optional[str] = None) -> List[Dict]:
        """Get products from cache."""
        if category_id:
            key = f"{self.prefix}products:cat:{category_id}"
        else:
            key = f"{self.prefix}products:all"

        data = self.redis.get(key)
        return json.loads(data) if data else []

    def set_products(self, products: List[Dict], category_id: Optional[str] = None, ttl: int = 3600):
        """Cache products."""
        if category_id:
            key = f"{self.prefix}products:cat:{category_id}"
        else:
            key = f"{self.prefix}products:all"

        self.redis.setex(key, ttl, json.dumps(products))

    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get single product from cache."""
        products = self.get_products()
        for prod in products:
            if prod.get("id") == product_id:
                return prod
        return None
