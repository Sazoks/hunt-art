import json
from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model

from apps.websockets.subsystems import BaseWebSocketSubsystem

from ...models import (
    Chat,
    ChatMember,
    ChatMessage,
    GroupChatData,
    PersonalChatData,
)
from .message_receiver import ChatMessageReceiver


class ChatWebSocketSubsystem(BaseWebSocketSubsystem):
    """
    Подсистема для обработки веб-сокетных сообщений для чата.
    """

    def __init__(self, consumer: AsyncJsonWebsocketConsumer) -> None:
        super().__init__(consumer)
        self._message_receiver = ChatMessageReceiver(
            subsystem_name=self.get_subsystem_name(),
            consumer=consumer,
        )

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
        await self._message_receiver.receive(content)

    async def new_message(self, content: dict[str, Any]) -> None:
        await self.consumer.send_json(content)

    # async def read_message(self, content: dict[str, Any]) -> None:
    #     """
    #     Прочтение сообщения юзером.

    #     ```
    #     content = {
    #         "subsystem": "chat",
    #         "action": "read_message",
    #         "headers": {
    #             "jwt_access": "alskdfj;lwken,zxcmv",
    #         },
    #         "data": {
    #             "user_id": 5,
    #             "message_id": 123,
    #         },
    #     }
    #     ```
    #     """
