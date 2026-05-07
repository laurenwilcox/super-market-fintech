# -*- coding: utf-8 -*-
"""
Telegram Bot Configuration
"""

import os
from django.conf import settings
from core.models import AppConfiguration


class BotConfig:
    """Telegram bot configuration."""

    @classmethod
    def get_token(cls) -> str:
        """Get bot token from AppConfiguration."""
        config = AppConfiguration.get_config()
        return config.bot_token

    @classmethod
    def get_username(cls) -> str:
        """Get bot username from AppConfiguration."""
        config = AppConfiguration.get_config()
        return config.bot_username

    @classmethod
    def get_welcome_message(cls) -> str:
        """Get welcome message."""
        config = AppConfiguration.get_config()
        return config.welcome_message

    @classmethod
    def get_help_message(cls) -> str:
        """Get help message."""
        config = AppConfiguration.get_config()
        return config.help_message
