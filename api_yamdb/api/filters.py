from django_filters import rest_framework as filters
from reviews.models import Title


class CharFilterInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class TitleFilter(filters.FilterSet):
    category = CharFilterInFilter(
        field_name='category__slug',
        lookup_expr='in',
    )
    genre = CharFilterInFilter(
        field_name='genre__slug',
        lookup_expr='in',

    )

    class Meta:
        model = Title
        fields = (
            'genre',
            'category',
            'year',
            'name',
        )
