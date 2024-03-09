from django.urls import path

from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from . import views


router = SimpleRouter()
router.register(r'', views.ArtViewSet, basename='art')

comments_router = NestedSimpleRouter(router, r'', lookup='art')
comments_router.register(r'comments', views.ArtCommentsViewSet, basename='comment')


urlpatterns = [
    *router.urls,
    *comments_router.urls,
]
