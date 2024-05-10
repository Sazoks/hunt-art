from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chats"
    verbose_name = _("Чаты")
