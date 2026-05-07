# -*- coding: utf-8 -*-
"""
Resilient LOLZTEAM API Client with rate limiting and retries.
Handles all API communication with built-in error handling.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from core.models import AppConfiguration
from core.enums import ReasonCode
from .rate_limiter import RateLimiter
from .backoff import ExponentialBackoff
from .http_status_mapper import (
    map_http_status_to_reason_code,
    is_retryable_status,
    is_server_error
)

logger = logging.getLogger(__name__)


class LolzteamAPIClient:
    """Resilient client for LOLZTEAM Market API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """Initialize API client with configuration."""
        config = AppConfiguration.get_config()

        self.api_key = api_key or config.lolzteam_api_key
        self.api_url = api_url or config.lolzteam_api_url
        self.timeout = timeout or config.api_timeout_seconds

        self.rate_limiter = RateLimiter()
        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            max_retries=3
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'SuperMarket/1.0'
        }

    async def get_product(self, product_id: str) -> tuple[bool, dict]:
        """
        Fetch product from API.

        Returns:
            (success: bool, response: dict)
        """
        config = AppConfiguration.get_config()
        allowed, limiter_info = self.rate_limiter.is_allowed(
            config.rate_limit_requests,
            config.rate_limit_window_seconds
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded: {limiter_info}")
            return False, {
                'reason_code': ReasonCode.RATE_LIMIT,
                'reset_in_seconds': limiter_info.get('reset_in_seconds')
            }

        self.backoff.reset()
        endpoint = f"{self.api_url}/products/{product_id}"

        while self.backoff.should_retry():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        endpoint,
                        headers=self._get_headers()
                    )

                    if response.status_code == 200:
                        logger.info(f"Successfully fetched product {product_id}")
                        return True, {'data': response.json()}

                    reason_code = map_http_status_to_reason_code(response.status_code)

                    if is_retryable_status(response.status_code):
                        logger.warning(
                            f"Retryable error {response.status_code}, attempt {self.backoff.retry_count}"
                        )
                        await self.backoff.wait()
                        continue

                    logger.error(f"Non-retryable error: {response.status_code}")
                    return False, {'reason_code': reason_code}

            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {self.backoff.retry_count}")
                reason_code = ReasonCode.TIMEOUT

                if self.backoff.should_retry():
                    await self.backoff.wait()
                    continue

                return False, {'reason_code': reason_code}

            except httpx.NetworkError as e:
                logger.error(f"Network error: {str(e)}")
                reason_code = ReasonCode.NETWORK_ERROR

                if self.backoff.should_retry():
                    await self.backoff.wait()
                    continue

                return False, {'reason_code': reason_code}

        logger.error(f"Max retries exceeded for product {product_id}")
        return False, {'reason_code': ReasonCode.API_ERROR}

    async def list_products(self, category_id: str) -> tuple[bool, dict]:
        """
        Fetch products list from API.

        Returns:
            (success: bool, response: dict)
        """
        config = AppConfiguration.get_config()
        allowed, limiter_info = self.rate_limiter.is_allowed(
            config.rate_limit_requests,
            config.rate_limit_window_seconds
        )

        if not allowed:
            return False, {
                'reason_code': ReasonCode.RATE_LIMIT,
                'reset_in_seconds': limiter_info.get('reset_in_seconds')
            }

        self.backoff.reset()
        endpoint = f"{self.api_url}/categories/{category_id}/products"

        while self.backoff.should_retry():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        endpoint,
                        headers=self._get_headers()
                    )

                    if response.status_code == 200:
                        logger.info(f"Successfully fetched products for category {category_id}")
                        return True, {'data': response.json()}

                    reason_code = map_http_status_to_reason_code(response.status_code)

                    if is_retryable_status(response.status_code):
                        await self.backoff.wait()
                        continue

                    return False, {'reason_code': reason_code}

            except (httpx.TimeoutException, httpx.NetworkError):
                if self.backoff.should_retry():
                    await self.backoff.wait()
                    continue
                return False, {'reason_code': ReasonCode.TIMEOUT}

        return False, {'reason_code': ReasonCode.API_ERROR}
