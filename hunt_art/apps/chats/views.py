import time
from django.shortcuts import render

from apps.users.models import User

from .models import Chat, ChatMember, ChatMessage


def index(request):
    # chat = Chat.objects.first()
    # user = User.objects.filter(is_superuser=True).first()

    # x = chat.members.all()
    # print(x)

    # y = user.chats.all()
    # print(y)

    # x = chat.chat_members.all()
    # print(x)

    # y = user.member_in_chats.all()
    # print(y)

    return render(request, "chats/index.html")


def room(request, room_name):
    return render(request, "chats/room.html", {"room_name": room_name})
