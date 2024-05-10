from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


UserModel = get_user_model()


class WebsocketData(models.Model):
    user = models.OneToOneField(
        to=UserModel,
        on_delete=models.CASCADE,
        related_name="websocket_data",
        related_query_name="websocket_data",
    )
    channel_name = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Данные о веб-сокете пользователя")
        verbose_name = _("Данные о веб-сокетах пользователей")
