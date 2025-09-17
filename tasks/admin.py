from django.contrib import admin
from .models import Task, ActivityLog

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "user", "category", "due_date", "created_at")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "category", "created_at")

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "user", "action", "timestamp")
    search_fields = ("action", "task__title", "user__email")
    list_filter = ("action", "timestamp")
