import json
from typing import Any
from enum import Enum, auto

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from apps.websockets.subsystems import BaseWebSocketSubsystem
from apps.users.models import User

from .message_reader import ChatMessageReader

from ...models import (
    Chat,
    ChatMember,
    ChatMessage,
    GroupChatData,
    PersonalChatData,
)


class ChatWebSocketSubsystem(BaseWebSocketSubsystem):
    """
    Подсистема для обработки веб-сокетных сообщений для чата.
    """

    class ChatMessageType(Enum):
        TO_USER = auto()
        TO_CHAT = auto()

    def __init__(self, consumer: AsyncJsonWebsocketConsumer) -> None:
        super().__init__(consumer)
        self._message_reader = ChatMessageReader(consumer)

    @classmethod
    def get_subsystem_name(cls) -> str:
        return "chat"
    
    @classmethod
    def needs_to_reconnect_when_user_auth(cls) -> bool:
        return True
    
    async def handle_connect(self) -> None:
        if self.consumer.user is None:
            return
        
        async for chat in self.consumer.user.chats.all():
            await self.consumer.channel_layer.group_add(
                f'chat_pk_{chat.pk}',
                self.consumer.channel_name,
            )
    
    async def handle_disconnect(self) -> None:
        if self.consumer.user is None:
            return
        
        for chat in self.consumer.user.chats.all():
            await self.consumer.channel_layer.group_discard(
                f'chat_pk_{chat.pk}',
                self.consumer.channel_name,
            )

    async def receive_message(self, content: dict[str, Any]) -> None:
        """
        Обработка сообщения из чата.
        
        ```
        content = {
            'subsystem': 'chat',
            'action': 'receive_message',
            'headers': {
                'jwt_access': 'l3k2qjer,msdafnm;lkja3w4ras;df',
            },
            'data': {
                # При отправке в персональный чат.
                'user_id': 3,
                # При отправке сообщения в групповой чат.
                'chat_id': 5,
                'message_text': 'Some text',
            },
        }
        ```
        """
        self._validate_message(content)

        match self._get_chat_message_type(content):
            case self.ChatMessageType.TO_USER:
                await self._send_to_user(content)
            case self.ChatMessageType.TO_CHAT:
                await self._send_to_chat(content)
    
    def _validate_message(self, content: dict[str, Any]) -> None:
        data: dict[str, Any] = content['data']
        if data.get("user_id") and data.get("chat_id"):
            # TODO: Сделать норм исключение.
            raise ValueError("Может быть либо user_id, либо chat_id.")
        
        # TODO: Сделать другие проверки.
        
    def _get_chat_message_type(self, content: dict[str, Any]) -> ChatMessageType:
        data: dict[str, Any] = content['data']
        chat_message_type = self.ChatMessageType.TO_USER if data.get('user_id') is not None else self.ChatMessageType.TO_CHAT
        return chat_message_type
    
    async def _send_to_user(self, content: dict[str, Any]) -> None:
        data: dict[str, Any] = content["data"]

        # TODO: При ненахождении юзера кидать норм ошибку.
        other_user: User = await User.objects.select_related('websocket_data').filter(pk=data['user_id']).aget()

        # TODO: Перенести это в какой-то обработчик, который требует аутентифицированного
        # юзера перед выполнением метода.
        current_user: User | None = self.consumer.user
        if current_user is None:
            raise ValueError("Необходимо аутентифицироваться.")
        
        # TODO: Сделать норм ошибку.
        if other_user.pk == current_user.pk:
            raise ValueError("Нельзя отправить сообщение самому себе.")

        personal_chat = await self._get_personal_chat_by_users(current_user, other_user)
        if personal_chat is None:
            personal_chat = await self._create_new_personal_chat(current_user, other_user)

        new_message = await ChatMessage.objects.acreate(
            chat=personal_chat,
            user=current_user,
            text=content['data']['message_text'],
        )

        # TODO: Сделать проверку разрешений:
        #   1. Пользователь не в бане у другого пользователя.
        
        await self._send_message_to_channel_layer(personal_chat, current_user, new_message)

    async def _send_to_chat(self, content: dict[str, Any]) -> None:
        # TODO: Реализовать в будущем.
        raise NotImplementedError()

    # NOTE: Синхронная функция используется только из-за intersection. Его нет в асинхронном варианте.
    @sync_to_async
    def _get_personal_chat_by_users(self, current_user: User, other_user: User) -> User | None:
        # У двух пользователей может быть только один ОБЩИЙ персональный чат.
        # Т.е. персональный чат с одним и тем же ID у двух пользователей.
        personal_chats: list[Chat] = list(
            current_user.chats
            .filter(chat_type=Chat.ChatType.PERSONAL)
            .intersection(
                other_user.chats
                .filter(chat_type=Chat.ChatType.PERSONAL)
            )
        )
        if len(personal_chats) == 0:
            return
        elif len(personal_chats) > 1:
            # TODO: Сделать норм исключение.
            raise ValueError("У двух пользователей может быть только один общий персональный чат.")
        
        return personal_chats[0]
    
    async def _create_new_personal_chat(self, current_user: User, other_user: User) -> Chat:
        new_chat = await Chat.objects.acreate(chat_type=Chat.ChatType.PERSONAL)
        await ChatMember.objects.abulk_create([
            ChatMember(chat=new_chat, user=current_user),
            ChatMember(chat=new_chat, user=other_user),
        ])

        # Добавим каналы двух юзеров в одну группу (в этот чат). Нужно, чтобы текущее (первое)
        # сообщение пришло обоим пользователям.
        await self.consumer.channel_layer.group_add(
            f'chat_pk_{new_chat.pk}',
            current_user.websocket_data.channel_name,
        )
        await self.consumer.channel_layer.group_add(
            f'chat_pk_{new_chat.pk}',
            other_user.websocket_data.channel_name,
        )

        return new_chat
    
    async def _send_message_to_channel_layer(self, chat: Chat, current_user: User, message: ChatMessage) -> None:
        await self.consumer.channel_layer.group_send(
            group=f"chat_pk_{chat.pk}",
            message={
                "type": "websocket.receive",
                "text": json.dumps({
                    "subsystem": self.get_subsystem_name(),
                    "action": "new_message",
                    "data": {
                        "message_id": message.pk,
                        "message_text": message.text,
                        "created_at": message.created_at.isoformat(),
                        "author": {
                            "id": current_user.pk,
                            "username": current_user.username,
                        },
                    },
                }),
            },
        )

    async def new_message(self, content: dict[str, Any]) -> None:
        await self.consumer.send_json(content)

    async def read_message(self, content: dict[str, Any]) -> None:
        """
        Прочтение сообщения юзером.

        ```
        content = {
            "subsystem": "chat",
            "action": "read_message",
            "headers": {
                "jwt_access": "alskdfj;lwken,zxcmv",
            },
            "data": {
                "user_id": 5,
                "message_id": 123,
            },
        }
        ```
        """
        # TODO: При ненахождении юзера кидать норм ошибку.
        other_user: User = await User.objects.select_related('websocket_data').filter(pk=content["data"]['user_id']).aget()

        # TODO: Перенести это в какой-то обработчик, который требует аутентифицированного
        # юзера перед выполнением метода.
        current_user: User | None = self.consumer.user
        if current_user is None:
            raise ValueError("Необходимо аутентифицироваться.")
        
        # TODO: Сделать норм ошибку.
        if other_user.pk == current_user.pk:
            raise ValueError("Нельзя отправить сообщение самому себе.")
        
        chat = await self._get_personal_chat_by_users(current_user, other_user)

        message_id = content["data"]["message_id"]
        message = await ChatMessage.objects.aget(pk=message_id)

        current_chat_member = await ChatMember.objects.filter(chat=chat, user=current_user).afirst()

        self._message_reader.read_message(message, current_chat_member)
