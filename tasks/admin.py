from django.contrib import admin
from activity.models import Task, ActivityLog

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "user", "category", "due_date", "created_at")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "category", "created_at")

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "get_task_title", "get_user_email", "action", "timestamp")
    search_fields = ("action", "task__title", "user__email")
    list_filter = ("action", "timestamp")

    def get_task_title(self, obj):
        return obj.task.title if obj.task else "-"
    get_task_title.short_description = "Task"

    def get_user_email(self, obj):
        return obj.user.email if obj.user else "-"
    get_user_email.short_description = "User"
