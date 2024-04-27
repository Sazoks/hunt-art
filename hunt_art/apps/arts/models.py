from enum import (
    auto,
    StrEnum,
)

from django.db import models
from django.contrib.postgres import (
    fields as pg_fields,
    indexes as pg_indexes,
)
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


UserModel = get_user_model()


class Art(models.Model):
    """Модель арта"""

    class AnnotatedFieldName(StrEnum):
        """Перечисление имен аннотируемых полей"""

        def _generate_next_value_(
            name: str, start: int,
            count: int, last_values: list[str],
        ) -> str:
            return name.lower()
        
        COUNT_LIKES = auto()

    author = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
        related_name='arts',
        related_query_name='art',
        verbose_name=_('Автор'),
    )
    image = models.ImageField(
        upload_to='arts/images',
        verbose_name=_('Изображение'),
    )
    description = models.TextField(
        max_length=10_000,
        blank=True,
        null=True,
        verbose_name=_('Описание'),
    )
    for_sale = models.BooleanField(
        default=False,
        verbose_name=_('На продажу'),
    )
    views = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_('Количество просмотров'),
    )
    tags = pg_fields.ArrayField(
        base_field=models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name=_('Тэги'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления'),
    )
    likes = models.ManyToManyField(
        to=UserModel,
        through='ArtLike',
        related_name='liked_arts',
        related_query_name='liked_art',
        verbose_name=_('Лайки'),
    )
    comments = models.ManyToManyField(
        to=UserModel,
        through='ArtComment',
        related_name='commented_arts',
        related_query_name='commented_art',
        verbose_name=_('Комментарии'),
    )

    class Meta:
        verbose_name = _('Арт')
        verbose_name_plural = _('Арты')
        indexes = (
            pg_indexes.GinIndex(fields=('tags', )),
        )

    def __str__(self) -> str:
        return f'Art#{self.pk} User#{self.author_id}'


class ArtLike(models.Model):
    """m2m модель лайков артов от пользователей"""

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
    )
    art = models.ForeignKey(
        to=Art,
        on_delete=models.CASCADE,
        verbose_name=_('Арт'),
    )

    class Meta:
        verbose_name = _('Лайк')
        verbose_name_plural = _('Лайки')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'art'),
                name='unique_user_art',
            ),
        )

    def __str__(self) -> str:
        return f'Like User#{self.user_id} Art#{self.art_id}'


class ArtComment(models.Model):
    """m2m модель комментариев артов от пользователей"""

    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
    )
    art = models.ForeignKey(
        to=Art,
        on_delete=models.CASCADE,
        verbose_name=_('Арт'),
    )
    text = models.TextField(
        max_length=4096,
        verbose_name=_('Текст комментария'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания'),
    )

    class Meta:
        verbose_name = _('Коментарий')
        verbose_name_plural = _('Коментарии')

    def __str__(self) -> str:
        return f'Comment User#{self.user_id} Art#{self.art_id}'
