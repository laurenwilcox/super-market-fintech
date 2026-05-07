# -*- coding: utf-8 -*-
"""
Token Bucket Rate Limiter using Redis.
Implements fixed-window rate limiting with token bucket algorithm.
"""

import redis
import time
from typing import Optional
from django.conf import settings
from core.enums import ReasonCode


class RateLimiter:
    """Token Bucket Rate Limiter using Redis backend."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limiter with Redis connection."""
        redis_url = redis_url or settings.REDIS_CORE_URL
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.bucket_key = "rate_limiter:tokens"
        self.reset_key = "rate_limiter:reset_at"

    def is_allowed(self, max_requests: int, window_seconds: int) -> tuple[bool, dict]:
        """
        Check if request is allowed within rate limit.

        Returns:
            (allowed: bool, info: dict) where info contains remaining tokens and reset time
        """
        current_time = time.time()
        reset_at = float(self.redis_client.get(self.reset_key) or current_time)

        if current_time >= reset_at:
            self.redis_client.set(self.bucket_key, max_requests)
            self.redis_client.set(self.reset_key, current_time + window_seconds)
            reset_at = current_time + window_seconds

        tokens = int(self.redis_client.get(self.bucket_key) or 0)

        if tokens > 0:
            self.redis_client.decr(self.bucket_key)
            remaining = int(self.redis_client.get(self.bucket_key) or 0)
            return True, {
                'remaining': remaining,
                'reset_at': int(reset_at),
                'reason': ReasonCode.SUCCESS
            }
        else:
            reset_in = int(reset_at - current_time)
            return False, {
                'remaining': 0,
                'reset_in_seconds': reset_in,
                'reason': ReasonCode.RATE_LIMIT
            }

    def reset(self):
        """Reset rate limiter state."""
        self.redis_client.delete(self.bucket_key)
        self.redis_client.delete(self.reset_key)
