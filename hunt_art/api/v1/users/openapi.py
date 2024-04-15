from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from utils.drf_spectacular import (
    OpenAPIDetailSerializer,
    OpenAPIDetailWithCodeSerializer,
    OpenAPIBadRequestSerializerFactory,
    get_pagination_schema,
)

from . import serializers


users_pagination_query_params = [
    OpenApiParameter(
        name='page',
        type=OpenApiTypes.STR,
        location='query',
        description=_(
            'Выбор страницы с пользователями.<br><br>'
            'Принимает целое число (номер страницы) либо `last` значение для выбора последней страницы.<br><br>'
            'Нумерация страниц начинается с `1`.<br><br>'
            'По умолчанию выбирает пользователей `первой` страницы.<br>'
        ),
    ),
    OpenApiParameter(
        name='page_size',
        description=_(
            'Указание размера страницы.<br><br>'
            'По умолчанию значение равно `30` пользователей на страницу.<br><br>'
            'Максимальный размер страницы: `100`.<br>'
        ),
        type=OpenApiTypes.INT,
        location='query',
    ),
]


users_openapi = {
    'list': extend_schema(
        operation_id='list_users',
        methods=('get', ),
        summary=_('Список пользователей'),
        description=_(
            'Получение списка пользователей.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
        ),
        parameters=users_pagination_query_params,
        auth=(),
        request=None,
        responses={
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'search_users': extend_schema(
        operation_id='search_users',
        methods=('get', ),
        summary=_('Поиск пользователей'),
        description=_(
            'Позволяет искать пользователей по `username`.<br><br>'
            'Поддерживает пагинацию по следующим параметрам: `page`, `page_size`.<br><br>'
            'Поддерживает поиск по следующим полям: `username`.<br><br>'
            'Выборка будет отсортирована по "возрастанию" имен пользователей.<br><br>'
            'Пример. Поиск идет по `svetla`. Тогда выборка может быть такой: `svetla`, `svetlan`, `svetlana`.<br>'
        ),
        parameters=[
            *users_pagination_query_params,
            OpenApiParameter(
                name='username',
                type=OpenApiTypes.STR,
                location='query',
                required=True,
                description=_('Поиск пользователей по `username`. Ищет пользователей, чей `username` начинается с указанного значения.<br>')
            ),
        ],
        request=None,
        responses={
            status.HTTP_200_OK: get_pagination_schema(
                name='PaginationSearchUsersSerializer',
                child_schema=serializers.ShortRetrieveUserSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        }
    ),
    'create': extend_schema(
        operation_id="create_user",
        methods=('post', ),
        summary=_("Регистрация пользователя"),
        description=_("Регистрация нового пользователя на основе имени и пароля."),
        auth=(),
        request=serializers.CreateUserSerializer,
        responses={
            status.HTTP_201_CREATED: serializers.CreateUserSerializer,
            status.HTTP_400_BAD_REQUEST: OpenAPIBadRequestSerializerFactory.create(
                name='BadRequestCreateUserSerializer',
                fields=('username', 'password'),
            ),
        },
    ),
    'retrieve': extend_schema(
        operation_id="retrieve_user",
        methods=('get', ),
        summary=_("Получение информации о пользователе"),
        description=_(
            'Получение информации о пользователе.<br><br>'
            'Поля `is_your_follower` и `is_your_subscription` доступны только тогда, '
            'когда запрос делает авторизированный пользователь. Иначе они просто отсутствуют.'
        ),
        auth=(),
        request=serializers.RetrieveUserForAuthorizedUserSerializer,
        responses={
            status.HTTP_200_OK: serializers.RetrieveUserForAuthorizedUserSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'current_user': extend_schema(
        operation_id="retrieve_current_user",
        methods=('get', ),
        summary=_("Получение информации о текущем пользователе"),
        description=_("Получение информации об авторизированном текущем пользователе."),
        request=serializers.RetrieveUserSerializer,
        responses={
            status.HTTP_200_OK: serializers.RetrieveUserSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
        },
    ),
    'update_current_user': extend_schema(
        operation_id="update_current_user",
        methods=('patch', ),
        summary=_("Обновление данных о текущем пользователе"),
        description=_("Обновление информации об авторизированном текущем пользователе."),
        request=serializers.UpdateUserSerializer,
        responses={
            status.HTTP_200_OK: serializers.UpdateUserSerializer,
            status.HTTP_400_BAD_REQUEST: OpenAPIBadRequestSerializerFactory.create(
                name='BadRequestUpdateUserSerializer',
                fields=('username', 'description', 'avatar', 'wallpaper', 'message'),
            ),
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
        },
    ),
    'subscribe_to_user': extend_schema(
        operation_id='subscribe_to_user',
        methods=('post', ),
        summary=_('Подписка на указанного пользователя'),
        description=_('Позволяет текущему авторизованному пользователю подписаться на указанного пользователя.'),
        request=None,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'unsubscribe_from_user': extend_schema(
        operation_id='unsubscribe_from_user',
        methods=('delete', ),
        summary=_('Отписка от указанного пользователя'),
        description=_('Позволяет текущему авторизованному пользователю отписаться от указанного пользователя.'),
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
    'remove_from_subscribers': extend_schema(
        operation_id='remove_from_subscribers',
        methods=('delete', ),
        summary=_('Удаление своего подписчика'),
        description=_('Позволяет текущему авторизованному пользователю удалить из подписчиков указанного пользователя.'),
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_403_FORBIDDEN: OpenAPIDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenAPIDetailSerializer,
        },
    ),
}


auth_openapi = {
    'token': extend_schema(
        operation_id='get_jwt_token',
        methods=('post', ),
        summary=_('Аутентификация'),
        description=_('Позволяет аутентифицироваться на основе логина и пароля и получить `access` и `refresh` токены.'),
        request=TokenObtainPairSerializer,
        responses={
            status.HTTP_200_OK: TokenObtainPairSerializer,
            status.HTTP_400_BAD_REQUEST: OpenAPIBadRequestSerializerFactory.create(
                name='BadRequestTokenSerializer',
                fields=('username', 'password'),
            ),
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailSerializer,
        },
    ),
    'token_refresh': extend_schema(
        operation_id='refresh_jwt_token',
        methods=('post', ),
        summary=_('Рефреш токена доступа'),
        description=_('Позволяет обновить токен доступа (`access`) с помощью рефреш-токена (`refresh`).'),
        request=TokenRefreshSerializer,
        responses={
            status.HTTP_200_OK: TokenRefreshSerializer,
            status.HTTP_400_BAD_REQUEST: OpenAPIBadRequestSerializerFactory.create(
                name='BadRequestTokenRefreshSerializer',
                fields=('refresh', ),
            ),
            status.HTTP_401_UNAUTHORIZED: OpenAPIDetailWithCodeSerializer,
        },
    ),
}
