import json
from typing import Any, Self, Type, Coroutine, Callable

from channels_redis.core import RedisChannelLayer
from channels.layers import get_channel_layer
from channels.consumer import get_handler_name
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chats.websockets.subsystems.chat import ChatWebSocketSubsystem
from apps.users.websockets.subsystems.auth import AuthWebSocketSubsystem
from apps.users.models import User

from .subsystems import BaseWebSocketSubsystem


class WebSocketConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.subsystems_by_name: dict[str, BaseWebSocketSubsystem] = {
            ChatWebSocketSubsystem.get_subsystem_name(): ChatWebSocketSubsystem(self),
            AuthWebSocketSubsystem.get_subsystem_name(): AuthWebSocketSubsystem(self),
        }
        self.user: User | None = None

    async def connect(self) -> None:
        for subsystem in self.subsystems_by_name.values():
            await subsystem.handle_connect()

        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        for subsystem in self.subsystems_by_name.values():
            await subsystem.handle_disconnect()

    async def receive_json(self, content: dict[str, Any]) -> None:
        """Прием и маршрутизация сообщений по подсистемам"""

        subsystem = self.subsystems_by_name[content["subsystem"]]
        action = content["action"]

        await AuthWebSocketSubsystem(self).auth(content)

        handler: Callable[[dict[str, Any]], Coroutine] = getattr(subsystem, action)
        await handler(content)
