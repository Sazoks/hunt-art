from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated

from apps.arts.models import Art


class IsArtOwner(IsAuthenticated):
    def has_object_permission(self, request: Request, view: APIView, obj: Art) -> bool:
        return request.user.pk == obj.author_id
