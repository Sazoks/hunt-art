from typing import Iterable
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer


class OpenAPIDetailSerializer(serializers.Serializer):
    """Сериализатор для сообщения с детялми ошибки"""

    detail = serializers.CharField()


class OpenAPIBadRequestSerializerFactory:
    """Фабрика сериализаторов для 400 ответа на основе набора полей"""

    @classmethod
    def create(
        cls, name: str, field_names: Iterable[str], **kwargs
    ) -> serializers.Serializer:
        """
        Создание класса сериализатора.

        :param name: Название сериализатора.
        :param field_names: Коллекция имен полей для сериализатора.
        """

        return inline_serializer(
            name=name,
            fields={
                field_name: serializers.ListField(
                    child=serializers.CharField(),
                    initial=["string"],
                )
                for field_name in field_names
            },
            **kwargs,
        )
