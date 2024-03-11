from typing import Iterable, Type
from rest_framework import serializers
from drf_spectacular.utils import inline_serializer


def get_pagination_schema(
    name: str,
    child_schema: Type[serializers.Serializer],
) -> serializers.Serializer:
    return inline_serializer(
        name=name,
        fields={
            'count': serializers.IntegerField(),
            'next': serializers.URLField(),
            'previous': serializers.URLField(),
            'results': child_schema(many=True),
        },
    )


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
