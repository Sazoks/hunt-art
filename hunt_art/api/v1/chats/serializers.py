from rest_framework import serializers

from apps.chats.models import (
    Chat,
    PersonalChatData,
    GroupChatData,
    ChatMember,
    ChatMessage,
)
from apps.users.models import User


class ShortChatSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    # chat_id = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    has_unread_messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            # "chat_type",
            # "chat_id",
            "user_id",
            "name",
            "avatar",
            "has_unread_messages",
        )

    def get_has_unread_messages(self, obj: Chat) -> bool:
        current_user: User = self.context['request'].user
        chat_member = ChatMember.objects.filter(chat=obj, user=current_user).first()
        if chat_member.read_before is None:
            return True
        return ChatMessage.objects.filter(chat=obj, created_at__gt=chat_member.read_before).exists()

    def get_name(self, obj: Chat) -> str:
        """
        Получение названия чата.
        
        Если чат персональный, название чата будет являться именем собеседника.
        Если чат групповой, у него есть собственное название.
        """

        if obj.chat_type == Chat.ChatType.PERSONAL:
            # Получим другого пользователя переписки.
            current_user = self.context["request"].user
            other_user = [
                user 
                for user in obj.users.all()
                if user.pk != current_user.pk
            ][0]
            return str(other_user.username) or None
        else:
            return str(obj.group_chat_data.name) or None

    def get_avatar(self, obj: Chat) -> str | None:
        """
        Получение аватарки чата.

        Если чат персональный, аватарка будет аватаркой собеседника текущего юзера.
        Если чат групповой, у такого чата есть своя собственная аватарка.
        """
        
        if obj.chat_type == Chat.ChatType.PERSONAL:
            # Получим другого пользователя переписки.
            current_user = self.context["request"].user
            other_user = [
                user 
                for user in obj.users.all()
                if user.pk != current_user.pk
            ][0]
            avatar = str(other_user.profile.avatar)
            if not avatar:
                return
            return self.context["request"].build_absolute_uri(other_user.profile.avatar.url)
        else:
            return self.context["request"].build_absolute_uri(obj.group_chat_data.avatar.url) or None

    def get_chat_id(self, obj: Chat) -> int | None:
        if obj.chat_type == Chat.ChatType.GROUP:
            return obj.pk
        
    def get_user_id(self, obj: Chat) -> int | None:
        if obj.chat_type == Chat.ChatType.PERSONAL:
            current_user = self.context["request"].user
            other_user = [
                user 
                for user in obj.users.all()
                if user.pk != current_user.pk
            ][0]
            return other_user.pk


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"
