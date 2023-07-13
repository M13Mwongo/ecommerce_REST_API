from django_filters import rest_framework as filters
from .models import Product


class ProductsFilter(filters.FilterSet):

    keyword = filters.CharFilter(field_name='name', lookup_expr='icontains')
    min_price = filters.NumberFilter(
        field_name='price' or 0, lookup_expr='gte')
    # price or integer specifies the min/max value to use in the filter
    max_price = filters.NumberFilter(
        field_name='price' or 10000000, lookup_expr='lte')

    class Meta:
        model = Product
        fields = ('keyword', 'category', 'brand', 'min_price', 'max_price')
