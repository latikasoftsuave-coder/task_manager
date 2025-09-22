from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')

app = Celery('task_manager')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-task-reminders-every-minute': {
        'task': 'tasks.tasks.send_due_reminders',
        'schedule': 60.0,  # every minute
    },
}

__all__ = ('app',)
