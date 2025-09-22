from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, DateFilter, ChoiceFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Task
from .serializers import TaskSerializer, ActivityLogSerializer, TaskCategorySerializer, TaskTagSerializer
from activity.models import ActivityLog
from categories.models import Category
from tags.models import Tag


class TaskFilter(FilterSet):
    """
    Explicit/structured filters for tasks list endpoint.
    - priority, status: Choice filters using Task model choices
    - category: match by category name (case-insensitive)
    - tags: comma-separated tag names -> tasks that have any of these tags
    - due_before, due_after: date filters against due_date
    """
    priority = ChoiceFilter(field_name="priority", choices=Task.PRIORITY_CHOICES, lookup_expr='iexact')
    status = ChoiceFilter(field_name="status", choices=Task.STATUS_CHOICES, lookup_expr='iexact')
    category = CharFilter(field_name="category__name", lookup_expr="iexact")
    tags = CharFilter(method='filter_tags')  # comma-separated names
    due_before = DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = DateFilter(field_name="due_date", lookup_expr="gte")

    class Meta:
        model = Task
        fields = ["priority", "status", "category", "tags", "due_before", "due_after"]

    def filter_tags(self, queryset, name, value):
        # allow comma-separated tag names: ?tags=Urgent,Important
        names = [t.strip() for t in value.split(",") if t.strip()]
        if not names:
            return queryset
        return queryset.filter(tags__name__in=names).distinct()


# Manual swagger parameters for list (so they appear in Swagger UI)
SWAGGER_TASK_LIST_PARAMS = [
    openapi.Parameter("priority", openapi.IN_QUERY, description="Filter by priority (High|Medium|Low)", type=openapi.TYPE_STRING),
    openapi.Parameter("status", openapi.IN_QUERY, description="Filter by status (Incomplete|Completed)", type=openapi.TYPE_STRING),
    openapi.Parameter("category", openapi.IN_QUERY, description="Filter by category name (case-insensitive)", type=openapi.TYPE_STRING),
    openapi.Parameter("tags", openapi.IN_QUERY, description="Filter by tag names (comma-separated)", type=openapi.TYPE_STRING),
    openapi.Parameter("due_before", openapi.IN_QUERY, description="Tasks due on or before date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
    openapi.Parameter("due_after", openapi.IN_QUERY, description="Tasks due on or after date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
]


class TaskViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for Task:
    - List (GET /tasks/) supports explicit filters: priority, status, category, tags, due_before, due_after
    - Create / Retrieve / Update / Delete operations
    - Extra actions: add-category, add-tag, logs, reminders
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    # Don't set a global queryset attribute because get_queryset customizes it per-user.
    def get_queryset(self):
        # When drf-yasg generates the schema it calls view methods without a real request.
        # Avoid evaluating `self.request.user` in that case.
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        return Task.objects.filter(user=self.request.user).distinct()

    @swagger_auto_schema(manual_parameters=SWAGGER_TASK_LIST_PARAMS)
    def list(self, request, *args, **kwargs):
        """List tasks (supports explicit filtering via query params)."""
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action="created",
            details={"title": task.title},
        )

    def perform_update(self, serializer):
        task = serializer.save()
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action="updated",
            details={"updated_fields": self.request.data},
        )

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        task = self.get_object()
        ActivityLog.objects.create(task=task, user=request.user, action="retrieved")
        return response

    # -------- CATEGORY --------
    @swagger_auto_schema(request_body=TaskCategorySerializer)
    @action(detail=True, methods=["post"], url_path="add-category")
    def add_category(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = get_object_or_404(Category, id=serializer.validated_data["category_id"])
        task.category = category
        task.save()
        ActivityLog.objects.create(task=task, user=request.user, action="category_added", details={"category": category.name})
        return Response({"task_id": str(task.id), "category_id": str(category.id), "category_name": category.name})

    # -------- TAGS --------
    @swagger_auto_schema(request_body=TaskTagSerializer)
    @action(detail=True, methods=["post"], url_path="add-tag")
    def add_tag(self, request, pk=None):
        task = self.get_object()
        serializer = TaskTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = Tag.objects.filter(id__in=serializer.validated_data["tags"])
        task.tags.set(tags)
        task.save()
        ActivityLog.objects.create(task=task, user=request.user, action="tag_added", details={"tags": [tag.name for tag in tags]})
        return Response({"task_id": str(task.id), "tags": [{"id": str(tag.id), "name": tag.name} for tag in tags]})

    # -------- LOGS --------
    @action(detail=True, methods=["get"], url_path="logs")
    def logs(self, request, pk=None):
        task = self.get_object()
        logs = ActivityLog.objects.filter(task=task, user=request.user).order_by("-timestamp")
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)

    # -------- REMINDERS (no extra structured filters here) --------
    @action(detail=False, methods=["get"], url_path="reminders")
    def reminders(self, request):
        now = timezone.now()
        tasks = Task.objects.filter(user=request.user, remind_at__isnull=False, remind_at__gte=now)
        reminders = [{"task_id": str(task.id), "title": task.title, "remind_at": task.remind_at} for task in tasks]
        return Response(reminders)
