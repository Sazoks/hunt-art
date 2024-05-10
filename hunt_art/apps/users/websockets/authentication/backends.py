from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Set

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.translation import gettext_lazy as _

from rest_framework import HTTP_HEADER_ENCODING

from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.models import TokenUser
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError

from ...models import User


# ==================================================================
# Эта часть скопирована из `rest_framework_simplejwt.authentication`.
# Функционал `JWTWebSocketAuthentication` также скопирован из 
# `rest_framework_simplejwt.authentication.JWTAuthentication` и адаптирован
# для работы в консьюмерах.

AUTH_HEADER_TYPES = api_settings.AUTH_HEADER_TYPES

if not isinstance(api_settings.AUTH_HEADER_TYPES, (list, tuple)):
    AUTH_HEADER_TYPES = (AUTH_HEADER_TYPES,)

AUTH_HEADER_TYPE_BYTES: Set[bytes] = {
    h.encode(HTTP_HEADER_ENCODING) for h in AUTH_HEADER_TYPES
}

AuthUser = TypeVar("AuthUser", AbstractBaseUser, TokenUser)

# ==================================================================


class BaseWebSocketAuthentication(ABC):
    @abstractmethod
    async def authenticate(self, content: dict[str, Any]) -> User:
        raise NotImplementedError()


class JWTWebSocketAuthentication(BaseWebSocketAuthentication):
    """
    Этот бэкенд аутентификации ожидает принять тело сообщения следующего вида:

    ```
    {
        ...,
        "headers": {
            "jwt_access": "eljkcvxlkealdsfkjxcvwe23nvIFSD3w0JS0",
        },
        ...,    
    }
    ```

    Если токен был предоставлен и аутентификация прошла успешно, в данных появится поле "user"
    с объектом пользователя.
    Если токен был предоставлен, но аутентификация закончилась ошибкой, будет ошибка.
    Если токен не был предоставлен, аутентификации не будет. Поля "user" в данных не будет.
    """

    queryset = User.objects.select_related("websocket_data")

    async def authenticate(self, content: dict[str, Any]) -> User:
        token = self.get_token_from_headers(content)
        if token is None:
            return None

        validated_token = self.get_validated_token(token)
        return await self.get_user(validated_token)

    def get_token_from_headers(self, scope: dict[str, Any]) -> str | None:   
        return scope.get("headers", {}).get("jwt_access")

    def get_validated_token(self, raw_token: bytes) -> Token:
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )

    async def get_user(self, validated_token: Token) -> AuthUser:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = await self.queryset.aget(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        if api_settings.CHECK_REVOKE_TOKEN:
            if validated_token.get(
                api_settings.REVOKE_TOKEN_CLAIM
            ) != get_md5_hash_password(user.password):
                raise AuthenticationFailed(
                    _("The user's password has been changed."), code="password_changed"
                )

        return user
