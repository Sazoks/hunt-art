from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from . import views


router = SimpleRouter()
router.register(
    prefix=r"",
    viewset=views.ChatsViewSet,
    basename="chat",
)

chat_messages_router = NestedSimpleRouter(router, r"", lookup="chat")
chat_messages_router.register(
    prefix=r"messages",
    viewset=views.ChatMessagesViewSet,
    basename="chatmessage",
)


urlpatterns = [
    *router.urls,
    *chat_messages_router.urls,
]
