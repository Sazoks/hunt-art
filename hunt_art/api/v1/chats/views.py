from typing import (
    Collection,
    Type,
)

from django.db.models import QuerySet

from rest_framework import mixins
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from apps.chats.models import (
    Chat,
    PersonalChatData,
    GroupChatData,
    ChatMember,
    ChatMessage,
)

from .pagination import ChatPagination, ChatMessagePagination
from .serializers import ShortChatSerializer, ChatMessageSerializer
from .openapi import chats_openapi, chat_messages_openapi


class ChatsViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    pagination_class = ChatPagination
    permissions_map: dict[str, Collection[BasePermission]] = {
        "list": (IsAuthenticated(), ),
    }

    def get_permissions(self) -> Collection[BasePermission]:
        return self.permissions_map.get(self.action, ())

    def get_serializer_class(self) -> Type[Serializer] | None:
        match self.action:
            case "list":
                return ShortChatSerializer
    
    def get_queryset(self) -> QuerySet[Chat]:
        """Чаты аутентифицированного пользователя"""
        return (
            self.request.user.chats
            .select_related("group_chat_data", "personal_chat_data")
            .prefetch_related("users")
            .all()
        )
    
    @chats_openapi.get("list")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)
    

class ChatMessagesViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = ChatMessageSerializer
    pagination_class = ChatMessagePagination
    permissions_map: dict[str, Collection[BasePermission]] = {
        "list": (IsAuthenticated(), ),
    }

    def get_queryset(self) -> QuerySet[ChatMessage]:
        return ChatMessage.objects.filter(chat_id=self.kwargs["chat_pk"]).order_by('-created_at')

    @chat_messages_openapi.get("list")
    def list(self, request: Request, *args, **kwargs) -> Response:
        return super().list(request, *args, **kwargs)
