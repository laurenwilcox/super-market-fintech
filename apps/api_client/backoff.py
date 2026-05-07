# -*- coding: utf-8 -*-
"""
Exponential Backoff + Jitter implementation.
Retry strategy for handling transient failures.
"""

import random
import time
from typing import Optional


class ExponentialBackoff:
    """Exponential backoff with jitter for retries."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
        jitter: bool = True
    ):
        """
        Initialize backoff strategy.

        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            max_retries: Maximum number of retries
            jitter: Add random jitter to avoid thundering herd
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.jitter = jitter
        self.retry_count = 0

    def get_delay(self) -> float:
        """Get delay for current retry attempt."""
        if self.retry_count >= self.max_retries:
            return None

        delay = min(self.base_delay * (2 ** self.retry_count), self.max_delay)

        if self.jitter:
            jitter_amount = random.uniform(0, delay * 0.1)
            delay = delay + jitter_amount

        self.retry_count += 1
        return delay

    def wait(self):
        """Wait for the calculated delay."""
        delay = self.get_delay()
        if delay is not None:
            time.sleep(delay)
        return delay

    def should_retry(self) -> bool:
        """Check if we should retry."""
        return self.retry_count < self.max_retries

    def reset(self):
        """Reset retry counter."""
        self.retry_count = 0
