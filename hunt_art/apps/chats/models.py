from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


UserModel = get_user_model()


class Chat(models.Model):
    class ChatType(models.TextChoices):
        GROUP = "group", _("Групповой чат")
        PERSONAL = "personal", _("Личный чат")

    chat_type = models.CharField(
        choices=ChatType.choices,
        default=ChatType.PERSONAL,
        verbose_name=_("Тип чата"),
    )
    users = models.ManyToManyField(
        to=UserModel,
        through="ChatMember",
        related_name="chats",
        related_query_name="chat",
        verbose_name=_("Участники чата"),
    )

    class Meta:
        verbose_name = _("Чат")
        verbose_name_plural = _("Чаты")


class GroupChatData(models.Model):
    """Данные, специфичные только для групповых чатов"""
    
    chat = models.OneToOneField(
        to=Chat,
        on_delete=models.CASCADE,
        related_name="group_chat_data",
        related_query_name="group_chat_data",
        verbose_name=_("Чат"),
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Название чата"),
    )
    avatar = models.ImageField(
        upload_to="chats/groups",
        null=True,
        blank=True,
        verbose_name=_("Аватар группы"),
    )


class PersonalChatData(models.Model):
    """Данные, специфичные только для персональных переписок"""

    # NOTE: На данном этапе персональные чаты не обладают
    #   никакими особыми настройками. Это просто два юзера
    #   и их сообщения.

    chat = models.OneToOneField(
        to=Chat,
        on_delete=models.CASCADE,
        related_name="personal_chat_data",
        related_query_name="personal_chat_data",
        verbose_name=_("Чат"),
    )


class ChatMember(models.Model):
    """
    Модель участника чата.

    Связывает юзера с определенным чатом и хранит
    настройки и разрешения касательно этого юзера
    в этом чате.
    """

    chat = models.ForeignKey(
        to=Chat,
        on_delete=models.CASCADE,
        related_name="chat_members",
        related_query_name="chat_member",
        verbose_name=_("Чат"),
    )
    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
        related_name="user_members",
        related_query_name="user_member",
        verbose_name=_("Пользователь"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата присоединения к чату"),
    )

    class Meta:
        verbose_name = _("Участник чата")
        verbose_name_plural = _("Участники чата")
        constraints = (
            models.UniqueConstraint(
                fields=("chat", "user"),
                name="chatmember_chat_user_unique",
            ),
        )


class ChatMessage(models.Model):
    chat = models.ForeignKey(
        to=Chat,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        related_query_name="chat_message",
        verbose_name=_("Чат"),
    )
    user = models.ForeignKey(
        to=UserModel,
        on_delete=models.CASCADE,
        related_name="member_messages",
        related_query_name="member_message",
        verbose_name=_("Пользователь"),
    )
    text = models.TextField(
        max_length=8192,
        blank=False,
        null=False,
        verbose_name=_("Текст сообщения"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания сообщения"),
    )

    class Meta:
        verbose_name = _("Сообщение чата")
        verbose_name_plural = _("Сообщения чатов")
