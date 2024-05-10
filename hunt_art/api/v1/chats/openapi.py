from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiRequest
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _

from utils.drf_spectacular import (
    OpenAPIDetailSerializer,
    OpenAPIBadRequestSerializerFactory,
    get_pagination_schema,
)

from . import serializers


chats_openapi = {
    'list': extend_schema(
        operation_id="chats_list",
        methods=('get', ),
        summary=_("Получение чатов пользователя"),
        description=_(
            'Позволяет получить список чатов в порядке последних сообщений: чаты со свежими сообщениями - в начале, с более старыми - в конце.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
        ),
        parameters=[
            OpenApiParameter(
                name='page',
                description=_(
                    'Выбор страницы с чатами.<br><br>'
                    'Принимает целое число (номер страницы) либо `last` значение для выбора последней страницы.<br><br>'
                    'Нумерация страниц начинается с `1`.<br><br>'
                    'По умолчанию выбирает чаты `первой` страницы.<br>'
                ),
                type=OpenApiTypes.STR,
                location='query',
            ),
            OpenApiParameter(
                name='page_size',
                description=_(
                    'Указание размера страницы.<br><br>'
                    'По умолчанию значение равно `20` чатов на страницу.<br><br>'
                    'Максимальный размер страницы: `50`.<br>'
                ),
                type=OpenApiTypes.INT,
                location='query',
            ),
        ],
        responses={
            # status.HTTP_200_OK: get_pagination_schema(
            #     name='ChatsPaginationSerializer',
            #     child_schema=serializers.ShortChatSerializer,
            # ),
            status.HTTP_200_OK: serializers.ShortChatSerializer,
        },
    ),
}


chat_messages_openapi = {
    'list': extend_schema(
        operation_id="chatmessages_list",
        methods=('get', ),
        summary=_("Получение сообщений чата"),
        description=_(
            'Позволяет получить список сообщений в порядке убывания даты: в начале - самые свежие сообщения, в конце - самые старые сообщения.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
        ),
        parameters=[
            OpenApiParameter(
                name='page',
                description=_(
                    'Выбор страницы с сообщениями.<br><br>'
                    'Принимает целое число (номер страницы) либо `last` значение для выбора последней страницы.<br><br>'
                    'Нумерация страниц начинается с `1`.<br><br>'
                    'По умолчанию выбирает сообщения `первой` страницы.<br>'
                ),
                type=OpenApiTypes.STR,
                location='query',
            ),
            OpenApiParameter(
                name='page_size',
                description=_(
                    'Указание размера страницы.<br><br>'
                    'По умолчанию значение равно `50` сообщений на страницу.<br><br>'
                    'Максимальный размер страницы: `200`.<br>'
                ),
                type=OpenApiTypes.INT,
                location='query',
            ),
        ],
        responses={
            # status.HTTP_200_OK: get_pagination_schema(
            #     name='ChatsPaginationSerializer',
            #     child_schema=serializers.ShortChatSerializer,
            # ),
            status.HTTP_200_OK: serializers.ChatMessageSerializer,
        },
    ),
}
