from typing import Any, Final

from rest_framework import serializers

from apps.arts import models
from api.v1.users.serializers import ShortRetrieveUserSerializer


class RetrieveArtSerializer(serializers.ModelSerializer):
    count_likes = serializers.IntegerField()
    author = ShortRetrieveUserSerializer()

    class Meta:
        model = models.Art
        fields = (
            'id',
            'author',
            'image',
            'description',
            'for_sale',
            'views',
            'tags',
            'created_at',
            'updated_at',
            'count_likes',
        )


class RetrieveArtForAuthorizedUserSerializer(RetrieveArtSerializer):
    liked_authorized_user = serializers.SerializerMethodField()

    class Meta(RetrieveArtSerializer.Meta):
        fields = tuple([
            *RetrieveArtSerializer.Meta.fields,
            'liked_authorized_user',
        ])
    
    def get_liked_authorized_user(self, obj: models.Art) -> bool:
        authorized_user = self.context['request'].user
        return obj.likes.through.objects.filter(
            user_id=authorized_user.pk,
            art_id=obj.pk,
        ).exists()


class ShortRetrieveArtSerializer(serializers.ModelSerializer):
    count_likes = serializers.IntegerField()

    class Meta:
        model = models.Art
        fields = (
            'id',
            'author',
            'image',
            'count_likes',
            'created_at',
        )


class ShortRetrieveArtForAuthorizedUserSerializer(ShortRetrieveArtSerializer):
    liked_authorized_user = serializers.SerializerMethodField()

    class Meta(ShortRetrieveArtSerializer.Meta):
        fields = tuple([
            *ShortRetrieveArtSerializer.Meta.fields,
            'liked_authorized_user',
        ])

    def get_liked_authorized_user(self, obj: models.Art) -> bool:
        authorized_user = self.context['request'].user
        return obj.likes.through.objects.filter(user_id=authorized_user.pk).exists()


class CreateArtSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Art
        fields = (
            'id',
            'image',
            'description',
            'for_sale',
            'tags',
            'author',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'author': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def create(self, validated_data: dict[str, Any]) -> models.Art:
        validated_data['author'] = self.context['request'].user
        return models.Art.objects.create(**validated_data)


class ArtCommentSerializer(serializers.ModelSerializer):
    user = ShortRetrieveUserSerializer(read_only=True)

    class Meta:
        model = models.ArtComment
        fields = (
            'id',
            'user',
            'art',
            'text',
            'created_at',
        )
        extra_kwargs = {
            'art': {'read_only': True},
        }

    def create(self, validated_data: dict[str, Any]) -> models.ArtComment:
        user = self.context['request'].user
        art_id = self.context['view'].kwargs['art_pk']

        return models.ArtComment.objects.create(
            user_id=user.pk,
            art_id=art_id,
            **validated_data,
        )
