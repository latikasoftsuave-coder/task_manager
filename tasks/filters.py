import django_filters
from django.db.models import Q
from .models import Task

class TaskFilter(django_filters.FilterSet):
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    search = django_filters.CharFilter(method='filter_search', label='Search title/description')

    class Meta:
        model = Task
        fields = ['priority', 'status', 'due_before', 'due_after']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )
