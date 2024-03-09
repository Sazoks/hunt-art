from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from utils.drf_spectacular import (
    OpenAPIDetailSerializer,
    OpenAPIDetailWithCodeSerializer,
    OpenAPIBadRequestSerializerFactory,
)

from . import serializers


users_openapi = {
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
                fields=(
                    'username',
                    ('profile', OpenAPIBadRequestSerializerFactory.create(
                        name='BadRequestUpdateProfileSerializer',
                        fields=('description', 'avatar', 'wallpaper'),
                    )),
                ),
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
