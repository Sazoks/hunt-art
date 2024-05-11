import asyncio
import datetime as dt

from ...models import ChatMessage


class MessageReader:
    def __init__(self, delay: int) -> None:
        self.__delay = delay
        self.__last_readed_message: ChatMessage | None = None
        self.__last_message_is_changed: bool = False

    def read_message(self, message: ChatMessage) -> None:
        if (
            self.__last_readed_message is None
            or message.created_at > self.__last_readed_message.created_at
        ):
            self.__last_readed_message = message
            self.__last_message_is_changed = True

    async def _save_in_db(self) -> None:
        ...
