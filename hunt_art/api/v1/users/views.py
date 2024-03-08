import logging
import traceback
from typing import (
    Type,
    Collection,
)

from django.db.models import QuerySet
from django.contrib.auth.models import AnonymousUser

from rest_framework import mixins
from rest_framework import status
from rest_framework import exceptions
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
)

from apps.users.models import User
from apps.users.services.subscriptions.exceptions import (
    UserIsNotFollower,
    UserIsAlreadyFollower,
)
from apps.users.services.subscriptions import UserSubscriptionsService

from drf_spectacular.utils import extend_schema_view

from .serializers import (
    CreateUserSerializer,
    UpdateUserSerializer,
    RetrieveUserSerializer,
    RetrieveUserForAuthorizedUserSerializer,
)
from .openapi import users_openapi, auth_openapi


logger = logging.getLogger(__name__)


# @extend_schema_view(**openapi.openapi_docs)
class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    """API для работы с пользователями и их профилями"""

    permissions_map: dict[str, Collection[Type[BasePermission]]] = {
        'default': (IsAuthenticated(), ),
        'create': ((~IsAuthenticated)(), ),
        'retrieve': (),
    }

    def get_permissions(self) -> Collection[BasePermission]:
        return self.permissions_map.get(
            self.action,
            self.permissions_map['default'],
        )

    def get_serializer_class(self) -> Type[Serializer] | None:
        match self.action:
            case 'retrieve':
                if isinstance(self.request.user, AnonymousUser):
                    return RetrieveUserSerializer
                return RetrieveUserForAuthorizedUserSerializer
            case 'create':
                return CreateUserSerializer
            case 'current_user':
                return RetrieveUserSerializer
            case 'update_current_user':
                return UpdateUserSerializer

    def get_queryset(self) -> QuerySet[User]:
        queryset = User.objects.all()
        match self.action:
            case 'retrieve' | 'current_user':
                queryset = (
                    queryset
                    .select_related('profile')
                    .prefetch_related('followers', 'subscriptions')
                )
            case 'update_current_user':
                queryset = queryset.select_related('profile')

        return queryset
    
    @users_openapi.get('create')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @users_openapi.get('retrieve')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @users_openapi.get('current_user')
    @action(methods=('get', ), detail=False, url_path='im')
    def current_user(self, request: Request) -> Response:
        """Получение текущего авторизованного пользователя"""

        current_user_data = self.get_serializer(
            self.get_queryset().filter(pk=request.user.pk).first()
        ).data

        return Response(
            status=status.HTTP_200_OK,
            data=current_user_data,
        )
    
    @users_openapi.get('update_current_user')
    @current_user.mapping.patch
    def update_current_user(self, request: Request) -> Response:
        """Обновление текущего авторизованного пользователя"""

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    @users_openapi.get('subscribe_to_user')
    @action(methods=('post', ), detail=True, url_path='subscribe')
    def subscribe_to_user(self, request: Request, pk: int) -> Response:
        """API подписки на пользователя"""

        if request.user.pk == int(pk):
            raise exceptions.ValidationError(detail=f'Пользователь не может подписаться сам на себя.')

        try:
            other_user = User.objects.get(pk=pk)
            UserSubscriptionsService(request.user).subscribe_to_user(other_user)
        except User.DoesNotExist:
            raise exceptions.NotFound(detail=f'Пользователя с id={pk} не существует.')
        except UserIsAlreadyFollower as e:
            raise exceptions.PermissionDenied(detail=e.message)
        except Exception:
            logger.error(
                f'Ошибка при подписке пользователя {request.user} на пользователя {other_user}. '
                f'Ошибка:\n{traceback.format_exc()}'
            )
            raise exceptions.APIException()

        return Response(status=status.HTTP_200_OK)
    
    @users_openapi.get('unsubscribe_from_user')
    @action(methods=('delete', ), detail=True, url_path='unsubscribe')
    def unsubscribe_from_user(self, request: Request, pk: int) -> Response:
        """API отписки от пользователя"""

        if request.user.pk == int(pk):
            raise exceptions.ValidationError(detail=f'Пользователь не может отписаться сам от себя.')

        try:
            other_user = User.objects.get(pk=pk)
            UserSubscriptionsService(self.request.user).unsubscribe_from_user(other_user)
        except User.DoesNotExist:
            raise exceptions.NotFound(detail=f'Пользователя с id={pk} не существует.')
        except UserIsNotFollower as e:
            raise exceptions.PermissionDenied(detail=e.message)
        except Exception:
            logger.error(
                f'Ошибка при отписке пользователя {request.user} от пользователя {other_user}. '
                f'Ошибка:\n{traceback.format_exc()}'
            )
            raise exceptions.APIException()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @users_openapi.get('remove_from_subscribers')
    @action(methods=('delete', ), detail=True, url_path='remove-from-subscribers')
    def remove_from_subscribers(self, request: Request, pk: int) -> Response:
        """API удаления пользователя из своих подписчиков"""

        if request.user.pk == int(pk):
            raise exceptions.ValidationError(detail=f'Пользователь не является своим подписчиком.')

        try:
            other_user = User.objects.get(pk=pk)
            UserSubscriptionsService(self.request.user).remove_from_subscribers(other_user)
        except User.DoesNotExist:
            raise exceptions.NotFound(detail=f'Пользователя с id={pk} не существует.')
        except UserIsNotFollower as e:
            raise exceptions.PermissionDenied(detail=e.message)
        except Exception:
            logger.error(
                f'Ошибка при удалении пользователя {other_user} из подписчиков '
                f'пользователя {request.user}. Ошибка:\n{traceback.format_exc()}'
            )
            raise exceptions.APIException()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # # TODO: Убрать.
    # @action(methods=('post', ), detail=False, url_path='generate-users')
    # def generate(self, request: Request) -> Response:
    #     count = 1000
    #     users = [User(username=f'username_{i}', password='1234567') for i in range(count)]
    #     User.objects.bulk_create(users)
    #     return Response(status=200)


class CustomTokenObtainPairView(TokenObtainPairView):
    @auth_openapi.get('token')
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @auth_openapi.get('token_refresh')
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)
