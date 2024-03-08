from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator

import apps.users.managers as managers


class User(AbstractBaseUser, PermissionsMixin):
    """Модель пользователя"""

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        unique=True,
        verbose_name=_('username'),
        max_length=150,
        help_text=_(
            'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        ),
        validators=[username_validator],
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    subscriptions = models.ManyToManyField(
        to='User',
        blank=True,
        related_name='followers',
        related_query_name='subscription',
        verbose_name=_('Подписки'),
    )

    objects: managers.UserManager = managers.UserManager()

    EMAIL_FIELD = None
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class UserProfile(models.Model):
    """Модель профиля пользователя"""

    user = models.OneToOneField(
        to='User',
        on_delete=models.CASCADE,
        related_name='profile',
        related_query_name='profile',
        verbose_name=_('Пользователь'),
    )
    description = models.TextField(
        max_length=4096,
        blank=True,
        null=True,
        verbose_name=_('О себе'),
    )
    avatar = models.ImageField(
        upload_to='profiles/avatars',
        blank=True,
        null=True,
        verbose_name=_('Аватар'),
    )
    wallpaper = models.ImageField(
        upload_to='profiles/wallpapers',
        blank=True,
        null=True,
        verbose_name=_('Обои'),
    )

    class Meta:
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')

    def __str__(self) -> str:
        return f'Profile User #{self.user.pk}'


class PriceListImage(models.Model):
    """Модель прайс-листа пользователя"""

    profile = models.ForeignKey(
        to=UserProfile,
        on_delete=models.CASCADE,
        related_name='price_list',
        related_query_name='price_list',
    )
    image = models.ImageField(
        upload_to='profiles/price_list',
        verbose_name=_('Изображение прайс-листа'),
    )

    class Meta:
        verbose_name = _('Прайс-лист')
        verbose_name_plural = _('Прайс-листы')

    def __str__(self) -> str:
        return f'Price list Profile #{self.profile.pk}'
