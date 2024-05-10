from django.contrib import admin

from . import models


admin.site.register(models.ChatMember)
admin.site.register(models.ChatMessage)


class GroupChatDataInline(admin.StackedInline):
    model = models.GroupChatData
    extra = 1
    max_num = 1


class PersonalChatDataInline(admin.StackedInline):
    model = models.PersonalChatData
    extra = 1
    max_num = 1


@admin.register(models.Chat)
class ChatAdmin(admin.ModelAdmin):
    inlines = (
        GroupChatDataInline,
        PersonalChatDataInline,
    )
