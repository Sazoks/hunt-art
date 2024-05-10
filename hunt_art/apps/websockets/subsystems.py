from typing import Any, Type
from abc import ABC, abstractmethod

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BaseWebSocketSubsystem(ABC):
    """
    Подсистема для обработки веб-сокетных сообщений.
    """

    def __init__(self, consumer: AsyncJsonWebsocketConsumer) -> None:
        self.consumer = consumer

    @abstractmethod
    async def handle_connect(self) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    async def handle_disconnect(self) -> None:
        raise NotImplementedError()
    
    @classmethod
    def needs_to_reconnect_when_user_auth(cls) -> bool:
        return False

    @classmethod
    @abstractmethod
    def get_subsystem_name(cls) -> str:
        raise NotImplementedError()
