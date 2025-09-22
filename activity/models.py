import uuid
from django.db import models
from django.conf import settings
from tasks.models import Task


class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # e.g. created, updated, deleted
    details = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        task_title = self.task.title if self.task else "No Task"
        username = self.user.email if self.user else "No User"
        return f"{username} {self.action} {task_title} at {self.timestamp}"
