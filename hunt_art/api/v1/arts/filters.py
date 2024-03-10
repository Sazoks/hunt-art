from copy import copy

from django.forms import CharField
from django.http.request import QueryDict
from django_filters import rest_framework as filters
from django.contrib.postgres.forms.array import SimpleArrayField

from apps.arts.models import Art


class ArrayFilter(filters.Filter):
    field_class = SimpleArrayField


class ArtFilterSet(filters.FilterSet):
    tags = ArrayFilter(
        base_field=CharField(),
        lookup_expr='contains',
    )

    class Meta:
        model = Art
        fields = (
            'author',
            'for_sale',
            'tags',
        )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.__prepare_data()

    def __prepare_data(self) -> None:
        mutable_data: QueryDict = copy(self.data)

        self.__prepare_tags(mutable_data)

        self.data = mutable_data

    def __prepare_tags(self, mutable_data: QueryDict) -> None:
        # Данные под ключом tags предназначены для фильтра ArrayFilter с полем SimpleArrayField.
        # Это поле базируется на поле CharField и ожидает СТРОКУ вида
        # valu1,value2,valu3. По каким-то причинам, если передавать просто
        # исходное значение в виде list, это не работает. Идет фильтрация
        # по последнему элементу. Поэтому я вручную преобразовываю обратно в строку.
        # А уже само поле SimpleArrayField преобразовывает значения как надо.
        tags: list[str] = mutable_data.getlist('tags')
        mutable_data['tags'] = ','.join(tags)
