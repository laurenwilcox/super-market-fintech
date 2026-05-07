# -*- coding: utf-8 -*-
"""
HTTP status code to ReasonCode mapper.
Converts HTTP responses to domain-specific error codes.
"""

import httpx
from core.enums import ReasonCode


def map_http_status_to_reason_code(status_code: int) -> ReasonCode:
    """Map HTTP status code to domain ReasonCode."""

    if status_code == 200:
        return ReasonCode.SUCCESS
    elif status_code == 400:
        return ReasonCode.INVALID_ORDER
    elif status_code == 401:
        return ReasonCode.INVALID_USER
    elif status_code == 403:
        return ReasonCode.INVALID_USER
    elif status_code == 404:
        return ReasonCode.ITEM_NOT_AVAILABLE
    elif status_code == 429:
        return ReasonCode.RATE_LIMIT
    elif status_code == 500 or status_code == 502 or status_code == 503:
        return ReasonCode.API_ERROR
    elif status_code == 408 or status_code == 504:
        return ReasonCode.TIMEOUT
    elif status_code in (502, 503, 504):
        return ReasonCode.TIMEOUT
    else:
        return ReasonCode.UNKNOWN_ERROR


def is_retryable_status(status_code: int) -> bool:
    """Check if HTTP status code is retryable."""
    return status_code in (429, 500, 502, 503, 504)


def is_client_error(status_code: int) -> bool:
    """Check if HTTP status is client error (4xx)."""
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    """Check if HTTP status is server error (5xx)."""
    return 500 <= status_code < 600
