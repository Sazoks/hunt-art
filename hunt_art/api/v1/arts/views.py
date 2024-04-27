from typing import (
    Any,
    Type,
    Collection,
)
import contextlib

from django.db.models import (
    QuerySet,
    Subquery,
    Count,
    Model,
)
from django.contrib.auth.models import AnonymousUser
from django_filters import rest_framework as filters

from rest_framework import status
from rest_framework import mixins
from rest_framework import exceptions
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import GenericViewSet
from rest_framework.utils.mediatypes import media_type_matches

from apps.users.models import User
from apps.arts.models import (
    Art,
    ArtLike,
    ArtComment,
)

from . import openapi
from .serializers import (
    RetrieveArtSerializer,
    RetrieveArtForAuthorizedUserSerializer,
    CreateArtSerializer,
    ShortRetrieveArtSerializer,
    ShortRetrieveArtForAuthorizedUserSerializer,
    ArtCommentSerializer,
)
from .pagination import (
    ArtPagination,
    ArtCommentsPagination,
)
from .permissions import IsArtOwner
from .filters import ArtFilterSet


class ArtViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    pagination_class = ArtPagination
    permissions_map: dict[str, Collection[BasePermission]] = {
        'create': (IsAuthenticated(), ),
        'retrieve': (),
        'destroy': (IsArtOwner(), ),
        'new_arts': (),
        'subscriptions_arts': (IsAuthenticated(), ),
        'popular_arts': (),
        'like_art': (IsAuthenticated(), ),
        'dislike_art': (IsAuthenticated(), ),
        'user_arts': (),
    }
    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = ArtFilterSet

    def get_permissions(self) -> Collection[BasePermission]:
        return self.permissions_map.get(self.action, ())

    def get_serializer_class(self) -> Type[Serializer] | None:
        match self.action:
            case 'retrieve':
                if isinstance(self.request.user, AnonymousUser):
                    return RetrieveArtSerializer
                return RetrieveArtForAuthorizedUserSerializer
            
            case 'create':
                return CreateArtSerializer
            
            case 'new_arts' | 'subscriptions_arts' | 'popular_arts' | 'user_arts':
                if isinstance(self.request.user, AnonymousUser):
                    return ShortRetrieveArtSerializer
                return ShortRetrieveArtForAuthorizedUserSerializer

    def get_queryset(self) -> QuerySet[Art]:
        queryset = Art.objects.select_related('author')
        match self.action:
            case 'new_arts':
                queryset = (
                    queryset
                    .annotate(
                        **{Art.AnnotatedFieldName.COUNT_LIKES: Count('likes')},
                    )
                    .order_by('-created_at')
                )
            case 'subscriptions_arts':
                user_model_name = User._meta.model_name
                subscriptions_model: Model = User.subscriptions.through
                subscriber_field_name = f'from_{user_model_name}_id'
                subscription_field_name = f'to_{user_model_name}_id'
                queryset = (
                    queryset
                    .filter(
                        author_id__in=Subquery(
                            subscriptions_model.objects
                            .filter(**{subscriber_field_name: self.request.user.pk})
                            .values(subscription_field_name),
                        ),
                    )
                    .annotate(
                        **{Art.AnnotatedFieldName.COUNT_LIKES: Count('likes')},
                    )
                    .order_by('-created_at')
                )
            case 'popular_arts':
                queryset = (
                    queryset
                    .annotate(
                        **{Art.AnnotatedFieldName.COUNT_LIKES: Count('likes')},
                    )
                    .order_by(f'-{Art.AnnotatedFieldName.COUNT_LIKES}')
                )
            case 'user_arts':
                queryset = (
                    queryset
                    .filter(author_id=self.kwargs['user_id'])
                    .annotate(
                        **{Art.AnnotatedFieldName.COUNT_LIKES: Count('likes')},
                    )
                    .order_by('-created_at')
                )

        return queryset

    def get_object(self) -> Art:
        art: Art = super().get_object()
        if self.action == 'retrieve':
            # Получение лайков для одного арта будет быстрее в два запроса, чем в один.
            # (связано с тем, что JOIN'ы жрут много процессорного времени).
            count_likes = ArtLike.objects.filter(art_id=art.pk).count()
            art.__dict__[Art.AnnotatedFieldName.COUNT_LIKES] = count_likes

            art.views += 1
            art.save(update_fields=('views', ))

        return art
    
    def perform_authentication(self, request: Request) -> None:
        if self.action in ('retrieve', 'new_arts', 'popular_arts', 'user_arts'):
            with contextlib.suppress(exceptions.AuthenticationFailed):
                return super().perform_authentication(request)
        else:
            return super().perform_authentication(request)

    def post_parsing(self, request: Request) -> None:
        match self.action:
            # MultiPartParser не умеет правильно обрабатывать массивы, поэтому придется вручную делать это.
            # FIXME: Это жоский костыль, который надо исправить в будущем. Сделать более общее и модульное решение.
            case 'create' if media_type_matches(MultiPartParser.media_type, request.content_type):
                # Конвертируем строку в массив строк.
                incorrectly_parsed_tags: str = request.data.getlist('tags')[0]
                tags: list[str] = incorrectly_parsed_tags.split(',')

                # Удалим все пустые строки.
                tags = list(filter(lambda item: item != '', tags))

                request.data.setlist('tags', tags)

    def initialize_request(self, request: Request, *args, **kwargs) -> Request:
        request = super().initialize_request(request, *args, **kwargs)
        self.post_parsing(request)

        return request

    @openapi.arts_openapi.get('create')
    def create(self, request: Request, *args, **kwargs) -> Response:
        return super().create(request, *args, **kwargs)

    @openapi.arts_openapi.get('retrieve')
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)
    
    @openapi.arts_openapi.get('destroy')
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        return super().destroy(request, *args, **kwargs)
    
    @openapi.arts_openapi.get('new_arts')
    @action(methods=('get', ), detail=False, url_path='new')
    def new_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
    @openapi.arts_openapi.get('subscriptions_arts')
    @action(methods=('get', ), detail=False, url_path='subscriptions')
    def subscriptions_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
    @openapi.arts_openapi.get('popular_arts')
    @action(methods=('get', ), detail=False, url_path='popular')
    def popular_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
    @openapi.arts_openapi.get('user_arts')
    @action(methods=('get', ), detail=False, url_path='users/(?P<user_id>[^/.]+)')
    def user_arts(self, request: Request, user_id: Any) -> Response:
        return self._get_list_arts(request)
    
    def _get_list_arts(self, request: Request) -> Response:
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @openapi.arts_openapi.get('like_art')
    @action(methods=('post', ), detail=True, url_path='like')
    def like_art(self, request: Request, *args, **kwargs) -> Response:
        art = self.get_object()
        if ArtLike.objects.filter(user_id=request.user.pk, art_id=art.pk).exists():
            raise exceptions.PermissionDenied(
                f'Пользователь id={request.user.pk} уже лайкнул арт id={art.pk}'
            )

        ArtLike.objects.create(user_id=request.user.pk, art_id=art.pk)

        return Response(status=status.HTTP_200_OK)
    
    @openapi.arts_openapi.get('dislike_art')
    @like_art.mapping.delete
    def dislike_art(self, request: Request, *args, **kwargs) -> Response:
        art = self.get_object()
        if not ArtLike.objects.filter(user_id=request.user.pk, art_id=art.pk).exists():
            raise exceptions.PermissionDenied(
                f'Пользователь id={request.user.pk} не лайкал арт id={art.pk}'
            )
        
        ArtLike.objects.filter(user_id=request.user.pk, art_id=art.pk).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # # TODO: Убрать.
    # @action(methods=('post', ), detail=False, url_path='generate-likes')
    # def generate_likes(self, request: Request) -> Response:
    #     likes = [ArtLike(user_id=i, art_id=1) for i in range(2, 1002)]
    #     ArtLike.objects.bulk_create(likes)
    #     return Response(status=200)


class ArtCommentsViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    pagination_class = ArtCommentsPagination
    serializer_class = ArtCommentSerializer
    permissions_map: dict[str, Collection[BasePermission]] = {
        'create': (IsAuthenticated(), ),
        'list': (),
    }

    def get_permissions(self) -> Collection[BasePermission]:
        return self.permissions_map.get(self.action, ())

    def get_queryset(self) -> QuerySet[ArtComment]:
        return ArtComment.objects.filter(art_id=self.kwargs['art_pk']).order_by('-created_at')
    
    def perform_authentication(self, request: Request) -> None:
        if self.action in ('list', ):
            with contextlib.suppress(exceptions.AuthenticationFailed):
                return super().perform_authentication(request)
        else:
            return super().perform_authentication(request)

    @openapi.art_comments_openapi.get('create')
    def create(self, request: Request, *args, **kwargs) -> Response:
        self._check_art_exists()
        return super().create(request, *args, **kwargs)
    
    @openapi.art_comments_openapi.get('list')
    def list(self, request: Request, *args, **kwargs) -> Response:
        self._check_art_exists()
        return super().list(request, *args, **kwargs)

    def _check_art_exists(self) -> None:
        art_pk = self.kwargs['art_pk']
        if not Art.objects.filter(pk=art_pk).exists():
            raise exceptions.NotFound(f'Арта с id={art_pk} не существует.')
