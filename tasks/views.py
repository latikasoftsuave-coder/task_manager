from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Task
from activity.models import ActivityLog
from .serializers import (
    TaskSerializer,
    ActivityLogSerializer,
    TaskCategorySerializer,
    TaskTagSerializer,
)
from categories.models import Category
from tags.models import Tag
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# ---------- LIST + CREATE WITH FILTERING ----------
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("priority", openapi.IN_QUERY, description="Filter by priority", type=openapi.TYPE_STRING),
            openapi.Parameter("status", openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter("due_before", openapi.IN_QUERY, description="Due before (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter("due_after", openapi.IN_QUERY, description="Due after (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter("order_by", openapi.IN_QUERY, description="Sort by field", type=openapi.TYPE_STRING),
            openapi.Parameter("search", openapi.IN_QUERY, description="Search title/description", type=openapi.TYPE_STRING),
        ]
    )
    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)

        # Filtering
        priority = self.request.query_params.get("priority")
        status_filter = self.request.query_params.get("status")
        due_before = self.request.query_params.get("due_before")
        due_after = self.request.query_params.get("due_after")
        search = self.request.query_params.get("search")

        if priority:
            queryset = queryset.filter(priority=priority)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if due_before:
            queryset = queryset.filter(due_date__lte=due_before)
        if due_after:
            queryset = queryset.filter(due_date__gte=due_after)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # Sorting
        order_by = self.request.query_params.get("order_by")
        if order_by in ["priority", "due_date", "created_at", "-priority", "-due_date", "-created_at"]:
            queryset = queryset.order_by(order_by)

        return queryset

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action="created",
            details={"title": task.title},
        )


# ---------- DETAIL (Retrieve, Update, Delete) ----------
class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        task = self.get_object()
        ActivityLog.objects.create(task=task, user=request.user, action="retrieved")
        return response

    def update(self, request, *args, **kwargs):
        if request.method == "PUT":
            kwargs["partial"] = False
        elif request.method == "PATCH":
            kwargs["partial"] = True

        response = super().update(request, *args, **kwargs)
        task = self.get_object()
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action="updated",
            details={"updated_fields": request.data},
        )
        return response


# ---------- CATEGORY ----------
@swagger_auto_schema(
    method="post",
    request_body=TaskCategorySerializer,
    responses={200: "Category added successfully"},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_category_to_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    serializer = TaskCategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    category_id = serializer.validated_data["category_id"]
    category = get_object_or_404(Category, id=category_id)

    task.category = category
    task.save()

    ActivityLog.objects.create(
        task=task, user=request.user, action="category_added", details={"category": category.name}
    )

    return Response(
        {
            "task_id": str(task.id),
            "category_id": str(category.id),
            "category_name": category.name,
        }
    )


# ---------- TAGS ----------
@swagger_auto_schema(
    method="post",
    request_body=TaskTagSerializer,
    responses={200: "Tags added successfully"},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_tag_to_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    serializer = TaskTagSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    tag_ids = serializer.validated_data["tags"]
    tags = Tag.objects.filter(id__in=tag_ids)
    task.tags.set(tags)  # overwrite tags with new set
    task.save()

    ActivityLog.objects.create(
        task=task,
        user=request.user,
        action="tag_added",
        details={"tags": [tag.name for tag in tags]},
    )

    return Response(
        {
            "task_id": str(task.id),
            "tags": [{"id": str(tag.id), "name": tag.name} for tag in tags],
        }
    )


# ---------- LOGS ----------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def task_logs(request, task_id):
    logs = ActivityLog.objects.filter(task_id=task_id, user=request.user).order_by("-timestamp")
    if not logs.exists():
        return Response({"error": "No logs found for this task"}, status=404)
    serializer = ActivityLogSerializer(logs, many=True)
    return Response(serializer.data)


# ---------- REMINDERS ----------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reminders(request):
    now = timezone.now()
    tasks = Task.objects.filter(user=request.user, remind_at__isnull=False, remind_at__lte=now)
    reminders = [
        {"task_id": str(task.id), "title": task.title, "remind_at": task.remind_at}
        for task in tasks
    ]
    return Response(reminders)
