from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import Task, ActivityLog
from .serializers import TaskSerializer, ActivityLogSerializer
from categories.models import Category
from tags.models import Tag

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)

        # Filtering
        status_filter = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        category_id = self.request.query_params.get('category_id')
        tag_id = self.request.query_params.get('tag_id')
        search = self.request.query_params.get('search')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority:
            queryset = queryset.filter(priority=priority)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tag_id:
            queryset = queryset.filter(tags=tag_id)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        task = serializer.save()
        # Log activity
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action='created',
            details={'title': task.title}
        )

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        # enforce difference between PUT and PATCH
        if request.method == 'PUT':
            kwargs['partial'] = False   # full update required
        elif request.method == 'PATCH':
            kwargs['partial'] = True    # partial update allowed

        response = super().update(request, *args, **kwargs)

        # log update activity
        task = self.get_object()
        ActivityLog.objects.create(
            task=task,
            user=self.request.user,
            action='updated',
            details={'updated_fields': request.data}
        )

        return response

    def perform_destroy(self, instance):
        # log delete activity
        ActivityLog.objects.create(
            task=instance,
            user=self.request.user,
            action='deleted'
        )
        instance.delete()

@api_view(['POST'])
def add_category_to_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        category_name = request.data.get('category_name')

        category, created = Category.objects.get_or_create(name=category_name)
        task.category = category
        task.save()

        ActivityLog.objects.create(
            task=task,
            user=request.user,
            action='category_added',
            details={'category': category_name}
        )

        return Response({
            'task_id': str(task.id),
            'category_id': str(category.id),
            'category_name': category.name
        })
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)

@api_view(['POST'])
def add_tag_to_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        tag_name = request.data.get('tag_name')

        tag, created = Tag.objects.get_or_create(name=tag_name)
        task.tags.add(tag)

        ActivityLog.objects.create(
            task=task,
            user=request.user,
            action='tag_added',
            details={'tag': tag_name}
        )

        return Response({
            'task_id': str(task.id),
            'tags': [str(tag.id) for tag in task.tags.all()]
        })
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)

@api_view(['GET'])
def task_logs(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        logs = ActivityLog.objects.filter(task=task)
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)

@api_view(['POST'])
def set_reminder(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        remind_at = request.data.get('remind_at')

        task.remind_at = remind_at
        task.save()

        return Response({
            'task_id': str(task.id),
            'remind_at': task.remind_at
        })
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)

@api_view(['GET'])
def get_reminders(request):
    now = timezone.now()
    next_24h = now + timezone.timedelta(hours=24)

    tasks = Task.objects.filter(
        user=request.user,
        remind_at__isnull=False,
        remind_at__gte=now,
        remind_at__lte=next_24h
    )

    reminders = []
    for task in tasks:
        reminders.append({
            'task_id': str(task.id),
            'remind_at': task.remind_at
        })

    return Response(reminders)
