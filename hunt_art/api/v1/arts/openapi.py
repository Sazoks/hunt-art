from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _

from utils.drf_spectacular import (
    OpenAPIDetailSerializer,
    OpenAPIBadRequestSerializerFactory,
    get_pagination_schema,
)

from . import serializers


arts_list_query_params = [
    OpenApiParameter(
        name='page',
        description=_(
            'Выбор страницы с артами.<br><br>'
            'Принимает целое число (номер страницы) либо `last` значение для выбора последней страницы.<br><br>'
            'Нумерация страниц начинается с `1`.<br><br>'
            'По умолчанию выбирает арты `первой` страницы.<br>'
        ),
        type=OpenApiTypes.STR,
        location='query',
    ),
    OpenApiParameter(
        name='page_size',
        description=_(
            'Указание размера страницы.<br><br>'
            'По умолчанию значение равно `10` артов на страницу.<br><br>'
            'Максимальный размер страницы: `40`.<br>'
        ),
        type=OpenApiTypes.INT,
        location='query',
    ),
    OpenApiParameter(
        name='tags',
        description=_(
            'Фильтрация артов по тэгам.<br><br>'
            'Пример: `/api/v1/arts/new?tags=tag1&tags=tag2` - выберет все арты, в тэги которых входят тэги `tag1` и `tag2`.<br><br>'
        ),
        type=OpenApiTypes.STR,
        location='query',
        many=True,
    ),
    OpenApiParameter(
        name='author',
        description=_(
            'Фильтрация артов по имени автора.<br>'
        ),
        type=OpenApiTypes.STR,
        location='query',
    ),
    OpenApiParameter(
        name='for_sale',
        description=_(
            'Фильтрация артов на продажу или нет.<br>'
        ),
        type=OpenApiTypes.BOOL,
        location='query',
    ),
]


arts_openapi = {
    'create': extend_schema(
        operation_id="create_art",
        methods=('post', ),
        summary=_("Создание арта"),
        description=_("Позволяет создать арт."),
        request=serializers.CreateArtSerializer,
        responses={
            status.HTTP_201_CREATED: serializers.CreateArtSerializer,
            status.HTTP_400_BAD_REQUEST: OpenAPIBadRequestSerializerFactory.create(
                name='BadRequestCreateArtSerializer',
                fields=('image', 'description', 'for_sale', 'tags'),
            ),
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
        },
    ),
    'retrieve': extend_schema(
        operation_id="retrieve_art",
        methods=('get', ),
        summary=_("Получение информации об одном арте"),
        description=_(
            'Получение информации об одном арте.<br><br>'
            'Поле `liked_authorized_user` присутствует только если запрос делает авторизованный пользователь.<br><br>'
        ),
        auth=(),
        request=serializers.RetrieveArtForAuthorizedUserSerializer,
        responses={
            status.HTTP_200_OK: serializers.RetrieveArtForAuthorizedUserSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'destroy': extend_schema(
        operation_id="destroy_art",
        methods=('delete', ),
        summary=_("Удаление арта"),
        description=_(
            'Позволяет удалить арт.<br><br>'
            'Доступно, только если авторизованный пользователь удаляет свой арт. Иначе ошибка 403.<br><br>'
        ),
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'new_arts': extend_schema(
        operation_id="new_arts",
        methods=('get', ),
        auth=(),
        summary=_("Получение новых артов"),
        description=_(
            'Позволяет получить список артов в порядке их создания: от новых к старым.<br><br>'
            'Поле `liked_authorized_user` присутствует только если запрос делает авторизованный пользователь.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
            'Поддерживает фильтрацию по следующим параметрам: `tags`, `author`, `for_sale`.<br>'
        ),
        parameters=arts_list_query_params,
        responses={
            status.HTTP_200_OK: get_pagination_schema(
                name='NewArtsPaginationSerializer',
                child_schema=serializers.ShortRetrieveArtForAuthorizedUserSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'subscriptions_arts': extend_schema(
        operation_id="subscriptions_arts",
        methods=('get', ),
        summary=_("Получение артов из подписок"),
        description=_(
            'Позволяет получить список артов пользователей, на которых подписан авторизованный пользователь.<br><br>'
            'Арты также фильтруются по дате создания от новых к старым.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
            'Поддерживает фильтрацию по следующим параметрам: `tags`, `author`, `for_sale`.<br>'
        ),
        parameters=arts_list_query_params,
        responses={
            status.HTTP_200_OK: get_pagination_schema(
                name='SubscriptionsArtsPaginationSerializer',
                child_schema=serializers.ShortRetrieveArtForAuthorizedUserSerializer,
            ),
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
        },
    ),
    'popular_arts': extend_schema(
        operation_id="popular_arts",
        methods=('get', ),
        auth=(),
        summary=_("Получение популярных артов"),
        description=_(
            'Позволяет получить список артов в порядке их популярности: от более популярных к менее.<br><br>'
            'Популярность опредялется только на основе кол-ва лайков.<br><br>'
            'Поле `liked_authorized_user` присутствует только если запрос делает авторизованный пользователь.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
            'Поддерживает фильтрацию по следующим параметрам: `tags`, `author`, `for_sale`.<br>'
        ),
        parameters=arts_list_query_params,
        responses={
            status.HTTP_200_OK: get_pagination_schema(
                name='PopularArtsPaginationSerializer',
                child_schema=serializers.ShortRetrieveArtForAuthorizedUserSerializer,
            ),
        },
    ),
    'user_arts': extend_schema(
        operation_id="user_arts",
        methods=('get', ),
        auth=(),
        summary=_("Получение артов конкретного пользователя"),
        description=_(
            'Позволяет получить список артов конкретного пользователя в порядке их создания: от новых к старым.<br><br>'
            'Поле `liked_authorized_user` присутствует только если запрос делает авторизованный пользователь.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
            'Поддерживает фильтрацию по следующим параметрам: `tags`, `author`, `for_sale`.<br>'
        ),
        parameters=arts_list_query_params,
        responses={
            status.HTTP_200_OK: get_pagination_schema(
                name='UserArtsPaginationSerializer',
                child_schema=serializers.ShortRetrieveArtForAuthorizedUserSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'like_art': extend_schema(
        operation_id="like_art",
        methods=('post', ),
        summary=_("Поставить лайк указанному арту"),
        description=_(
            'Позволяет поставить лайк указанному арту.<br><br>'
            'Если пользователь уже ставил лайк, будет ошибка 403.<br><br>'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'dislike_art': extend_schema(
        operation_id="dislike_art",
        methods=('delete', ),
        summary=_("Удалить лайк у указанного арта"),
        description=_(
            'Позволяет удалить лайк у указанного арта.<br><br>'
            'Если пользователь не ставил лайк, будет ошибка 403.<br><br>'
        ),
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
}

art_comments_openapi = {
    'create': extend_schema(
        operation_id="create_art_comment",
        methods=('post', ),
        summary=_("Создать комментарий для указанного арта"),
        description=_(
            'Позволяет создать комментарий для указанного арта.<br><br>'
        ),
        responses={
            status.HTTP_201_CREATED: serializers.ArtCommentSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'list': extend_schema(
        operation_id="list_art_comment",
        methods=('get', ),
        auth=(),
        summary=_("Получение списка комментариев указанного арта"),
        description=_(
            'Позволяет получить список комментариев указанного арта в порядке их создания: от старых к новым.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`<br><br>'

        ),
        parameters=[
            OpenApiParameter(
                name='page',
                description=_(
                    'Выбор страницы с комментариями.<br><br>'
                    'Принимает целое число (номер страницы) либо `last` значение для выбора последней страницы.<br><br>'
                    'Нумерация страниц начинается с `1`.<br><br>'
                    'По умолчанию выбирает комментарии `первой` страницы.<br>'
                ),
                type=OpenApiTypes.STR,
                location='query',
            ),
            OpenApiParameter(
                name='page_size',
                description=_(
                    'Указание размера страницы.<br><br>'
                    'По умолчанию значение равно `30` комментариев на страницу.<br><br>'
                    'Максимальный размер страницы: `100`.<br>'
                ),
                type=OpenApiTypes.INT,
                location='query',
            ),
        ],
        responses={
            status.HTTP_200_OK: serializers.ArtCommentSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
}
