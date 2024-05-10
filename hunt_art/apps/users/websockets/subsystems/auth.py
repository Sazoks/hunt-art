from typing import (
    Any,
)

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.websockets.subsystems import BaseWebSocketSubsystem
from apps.websockets.models import WebsocketData

from ..authentication.backends import JWTWebSocketAuthentication, BaseWebSocketAuthentication


class AuthWebSocketSubsystem(BaseWebSocketSubsystem):
    def __init__(self, consumer: AsyncJsonWebsocketConsumer) -> None:
        super().__init__(consumer)
        self.auth_backends: list[BaseWebSocketAuthentication] = [
            JWTWebSocketAuthentication(),
        ]

    @classmethod
    def get_subsystem_name(cls) -> str:
        return "auth"
    
    async def handle_connect(self) -> None:
        pass

    async def handle_disconnect(self) -> None:
        pass

    async def auth(self, content: dict[str, Any]) -> None:
        """
        ```
        {
            "subsystem": "auth",
            "action": "auth,
            "headers": {
                "jwt_access": "asdfasd",
            },
        }
        ```
        """
        is_first_auth = self.consumer.user is None

        auth_error = False
        for backend in self.auth_backends:
            try:
                user = await backend.authenticate(content)
            except Exception:
                # TODO: Сделать норм обработку ошибок.
                auth_error = True
            else:
                auth_error = False
                break

        if auth_error:
            # Если была ошибка, вернем ее, но предварительно обнулим юзера.
            self.consumer.user = None
            # TODO: Сделать норм обработку ошибок.
            raise ValueError("Ошибка аутентификации")
        
        self.consumer.user = user

        # После аутентификации подсистемам может понадобиться еще раз выполнить
        # обработку подключения, чтобы инициализироваться с аутентифицированным юзером.
        # Переподключение подсистемы будет производиться только для первой аутентификации юзера.
        if is_first_auth:
            # Сохраним в БД для юзера айди его канала.
            await WebsocketData.objects.filter(user=user).aupdate(channel_name=self.consumer.channel_name)

            # Переподключим подсистемы.
            for subsystem in self.consumer.subsystems_by_name.values():
                subsystem: BaseWebSocketSubsystem
                if not subsystem.needs_to_reconnect_when_user_auth():
                    continue
                await subsystem.handle_connect()
