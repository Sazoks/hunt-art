from django.urls import (
    path,
    include,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
)
from rest_framework.routers import SimpleRouter

from . import views


router = SimpleRouter()
router.register(
    prefix=r'',
    viewset=views.UserViewSet,
    basename='user',
)


app_name = 'api_v1_users'
urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
