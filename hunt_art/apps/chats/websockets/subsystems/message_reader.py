import asyncio
import datetime as dt

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from ...models import ChatMessage, ChatMember


class ChatMessageReader:
    """
    Короче. Этот класс просто сохраняет последнее прочитанное сообщение. Проверяет,
    что новое сообщение должно быть старее, чем текущее сохраненное в памяти.

    Также экземпляр класса запускает в качестве фоновой задачи метод, которые раз в указанный
    промежуток времени в секундах обновляет у пользователя дату и время, до куда он дочитал.
    
    Т.е.по сути это некий баунсер. Нужен, чтобы не слишком спамить запросами.
    """
    
    def __init__(self, consumer: AsyncJsonWebsocketConsumer, delay: float = 1.0) -> None:
        self.__consumer = consumer
        self.__last_readed_message: ChatMessage | None = None
        self.__last_message_is_changed: bool = False

        # Запустим небольшую задачу, которая будет периодически проверять
        # последнее сообщение и делать запрос в БД.
        self.__delay = delay
        self.__task = asyncio.create_task(self._save_in_db())
        self.__chat_member: ChatMember | None = None

    def read_message(self, message: ChatMessage, chat_member: ChatMember) -> None:
        if (
            self.__last_readed_message is None
            or message.created_at > self.__last_readed_message.created_at
        ):
            self.__last_readed_message = message
            self.__last_message_is_changed = True
            self.__chat_member = chat_member

    async def _save_in_db(self) -> None:
        while True:
            await asyncio.sleep(self.__delay)
            if self.__last_readed_message is not None and self.__last_message_is_changed:
                self.__chat_member.read_before = self.__last_readed_message.created_at
                await self.__chat_member.asave(update_fields=("read_before", ))
