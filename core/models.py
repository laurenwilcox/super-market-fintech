from django.db import models
from django.core.exceptions import ValidationError


class AppConfiguration(models.Model):
    """
    Singleton model for storing dynamic application settings.
    Accessible via AppConfiguration.objects.get_or_create(pk=1) and then .get_config().
    """

    # Telegram Bot Settings
    bot_token = models.CharField(max_length=255, verbose_name="Telegram Bot Token")
    bot_username = models.CharField(max_length=100, verbose_name="Bot Username")

    # API Integration Settings
    lolzteam_api_key = models.CharField(max_length=255, verbose_name="LOLZTEAM API Key")
    lolzteam_api_url = models.URLField(default="https://api.lolzteam.net")

    # Redis Settings
    redis_core_url = models.CharField(
        max_length=500,
        default="redis://localhost:6379/0",
        verbose_name="Redis Core URL"
    )
    redis_cache_url = models.CharField(
        max_length=500,
        default="redis://localhost:6379/1",
        verbose_name="Redis Cache URL"
    )

    # Rate Limiting
    rate_limit_requests = models.IntegerField(default=100, verbose_name="Rate Limit Requests")
    rate_limit_window_seconds = models.IntegerField(default=60, verbose_name="Rate Limit Window (seconds)")

    # Timeouts
    api_timeout_seconds = models.IntegerField(default=30, verbose_name="API Timeout (seconds)")

    # Payment Settings
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        verbose_name="Minimum Order Amount"
    )
    max_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100000.00,
        verbose_name="Maximum Order Amount"
    )

    # Bot Messages (Dynamic)
    welcome_message = models.TextField(
        default="Добро пожаловать в магазин!",
        verbose_name="Welcome Message"
    )
    help_message = models.TextField(
        default="Используйте /help для списка команд",
        verbose_name="Help Message"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App Configuration"
        verbose_name_plural = "App Configuration"

    def clean(self):
        """Ensure only one instance exists."""
        if self.pk is None and AppConfiguration.objects.exists():
            raise ValidationError("Only one AppConfiguration instance is allowed")

    def save(self, *args, **kwargs):
        self.clean()
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AppConfiguration cannot be deleted")

    @classmethod
    def get_config(cls) -> 'AppConfiguration':
        """Get or create singleton instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"AppConfiguration (v{self.updated_at.timestamp()})"
