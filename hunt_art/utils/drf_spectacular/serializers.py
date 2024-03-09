from typing import Iterable
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer


class OpenAPIDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class OpenAPIDetailWithCodeSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField()


class OpenAPIBadRequestSerializerFactory:
    @classmethod
    def create(
        cls, name: str, fields: Iterable[str | tuple[str, serializers.Serializer]], **kwargs
    ) -> serializers.Serializer:
        """
        Создание класса сериализатора.

        :param name: Название сериализатора.
        :param field_names: Коллекция имен полей для сериализатора.
        """

        fields_: dict[str, serializers.Field] = {}
        for field in fields:
            if isinstance(field, str):
                fields_[field] = serializers.ListField(
                    child=serializers.CharField(),
                    initial=["string"],
                )
            elif isinstance(field, tuple):
                fields_[field[0]] = field[1]

        return inline_serializer(
            name=name,
            fields=fields_,
            **kwargs,
        )
