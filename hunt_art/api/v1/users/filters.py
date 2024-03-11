from django.db.models import QuerySet
from django_filters import rest_framework as filters

from apps.users.models import User


class UsersFilterSet(filters.FilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='startswith')

    class Meta:
        model = User
        fields = ('username', )

    def filter_queryset(self, queryset: QuerySet[User]) -> QuerySet[User]:
        # Фильтруем по возрастанию имени. Т.к. начало у всех будет одинаковое
        # благодаря `startswith`, фильтрация будет идти по длине имени.
        # В начале будет идти имя, полностью совпадающее с запросом.
        return super().filter_queryset(queryset).order_by('username')
