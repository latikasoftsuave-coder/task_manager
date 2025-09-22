# tasks/tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from .models import Task

@shared_task
def send_due_reminders():
    now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
    next_minute = now + timezone.timedelta(minutes=1)

    due_tasks = Task.objects.filter(remind_at__gte=now, remind_at__lt=next_minute, reminder_sent=False)

    print(f"[Celery] Checked at {now}, found {due_tasks.count()} tasks")

    for task in due_tasks:
        send_mail(
            subject=f"Reminder: {task.title}",
            message=f"Your task '{task.title}' is due now.",
            from_email="yourapp@example.com",
            recipient_list=[task.user.email],
            fail_silently=False,
        )
        task.reminder_sent = True
        task.save(update_fields=['reminder_sent'])
        print(f"[Celery] Sent reminder for task: {task.title}")
