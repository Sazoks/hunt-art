from typing import (
    Any,
    Type,
    Collection,
)

from django.db.models import (
    QuerySet,
    Subquery,
    Count,
    Model,
)
from django.contrib.auth.models import AnonymousUser
from django_filters import rest_framework as filters, utils

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
from rest_framework.viewsets import GenericViewSet

from apps.users.models import User

from apps.arts.models import (
    Art,
    ArtLike,
    ArtComment,
)

from .serializers import (
    RetrieveArtSerializer,
    RetrieveArtForAuthorizedUserSerializer,
    CreateArtSerializer,
    ShortRetrieveArtSerializer,
    ShortRetrieveArtForAuthorizedUserSerializer,
    ArtCommentSerializer,
)
from .paginations import (
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
        queryset = Art.objects.all()
        match self.action:
            case 'retrieve':
                queryset = queryset.select_related('author')
            case 'destory':
                queryset = Art.objects.filter(author_id=self.request.user.pk)
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
            art.save()

        return art
    
    @action(methods=('get', ), detail=False, url_path='new')
    def new_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
    @action(methods=('get', ), detail=False, url_path='subscriptions')
    def subscriptions_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
    @action(methods=('get', ), detail=False, url_path='popular')
    def popular_arts(self, request: Request) -> Response:
        return self._get_list_arts(request)
    
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

    @action(methods=('post', ), detail=True, url_path='like')
    def like_art(self, request: Request, *args, **kwargs) -> Response:
        art = self.get_object()
        if ArtLike.objects.filter(user_id=request.user.pk, art_id=art.pk).exists():
            raise exceptions.PermissionDenied(
                f'Пользователь id={request.user.pk} уже лайкнул арт id={art.pk}'
            )

        ArtLike.objects.create(user_id=request.user.pk, art_id=art.pk)

        return Response(status=status.HTTP_200_OK)
    
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
        return ArtComment.objects.filter(art_id=self.kwargs['art_pk']).order_by('created_at')

    def create(self, request: Request, *args, **kwargs) -> Response:
        self._check_art_exists()
        return super().create(request, *args, **kwargs)
    
    def list(self, request: Request, *args, **kwargs) -> Response:
        self._check_art_exists()
        return super().list(request, *args, **kwargs)

    def _check_art_exists(self) -> None:
        art_pk = self.kwargs['art_pk']
        if not Art.objects.filter(pk=art_pk).exists():
            raise exceptions.NotFound(f'Арта с id={art_pk} не существует.')
