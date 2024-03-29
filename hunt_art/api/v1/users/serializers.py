from typing import Any, Type

from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.request import Request

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.base_user import AbstractBaseUser

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from apps.users.models import (
    User,
    UserProfile,
)


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""

    def create(self, validated_data: dict[str, Any]) -> AbstractBaseUser:
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class ShortRetrieveUserSerializer(serializers.ModelSerializer):
    """Сериализатор с короткой информацией о пользователе"""

    class Meta:
        model = User
        fields = ('id', 'username')


class RetrieveUserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения данных о пользователе"""
        
    class _UserProfileSerializer(serializers.ModelSerializer):
        class Meta:
            model = UserProfile
            fields = '__all__'

    profile = _UserProfileSerializer()
    followers = ShortRetrieveUserSerializer(many=True)
    followers_count = serializers.SerializerMethodField()
    subscriptions = ShortRetrieveUserSerializer(many=True)
    subscriptions_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'is_active',
            'last_login',
            'profile',
            'followers',
            'followers_count',
            'subscriptions',
            'subscriptions_count',
        )

    @extend_schema_field(OpenApiTypes.INT)
    def get_followers_count(self, obj: User) -> int:
        return len(obj.followers.all())
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_subscriptions_count(self, obj: User) -> int:
        return len(obj.subscriptions.all())

    

class RetrieveUserForAuthorizedUserSerializer(RetrieveUserSerializer):
    """
    Сериализатор для получения данных о пользователе, если текущий пользователь
    является авторизованным.

    Кроме основной информации добавляются поля `is_your_follower` и `is_your_subscription`,
    позволяющие определить, является ли запрашиваемый пользователь подписчиком или подпиской
    для авторизованного пользователя (который делает запрос).
    """

    is_your_follower = serializers.SerializerMethodField()
    is_your_subscription = serializers.SerializerMethodField()

    class Meta(RetrieveUserSerializer.Meta):
        fields = tuple([
            *RetrieveUserSerializer.Meta.fields,
            'is_your_follower',
            'is_your_subscription',
        ])

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_your_follower(self, obj: User) -> bool:
        current_authorized_user = self.context['request'].user
        if current_authorized_user.pk == obj.pk:
            return False
        
        result = obj.subscriptions.filter(pk=current_authorized_user.pk).exists()

        return result

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_your_subscription(self, obj: User) -> bool:
        current_authorized_user = self.context['request'].user
        if current_authorized_user.pk == obj.pk:
            return False
        
        result = current_authorized_user.subscriptions.filter(pk=obj.pk).exists()

        return result


class UpdateUserSerializer(serializers.Serializer):
    """Сериализатор при обновлении данных пользователя"""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    avatar = serializers.ImageField(required=False, write_only=True)
    wallpaper = serializers.ImageField(required=False, write_only=True)

    _user_fields = ('username', )
    _profile_fields = ('description', 'avatar', 'wallpaper')

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if len(attrs) == 0:
            raise exceptions.ValidationError(
                detail={'message': 'Хотя бы одно поле должно быть заполнено.'},
            )

        return super().validate(attrs)

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        user_data = {
            field_name: validated_data[field_name]
            for field_name in self._user_fields
            if validated_data.get(field_name)
        }
        profile_data = {
            field_name: validated_data[field_name]
            for field_name in self._profile_fields
            if validated_data.get(field_name)
        }

        if len(user_data) > 0:
            for field_name, field_value in user_data.items():
                setattr(instance, field_name, field_value)
            instance.save()

        if len(profile_data) > 0:
            for field_name, field_value in profile_data.items():
                setattr(instance.profile, field_name, field_value)
            instance.profile.save()

        return instance
