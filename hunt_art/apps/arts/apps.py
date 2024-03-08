from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ArtsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.arts'
    verbose_name = _('Арты')
