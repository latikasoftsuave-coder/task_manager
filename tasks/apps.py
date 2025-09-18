from django.apps import AppConfig
import os


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        # Prevent scheduler from running twice in Django autoreloader
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        from .jobs import start_scheduler
        try:
            start_scheduler()
            print("✅ APScheduler started")
        except Exception as e:
            print(f"⚠️ APScheduler failed to start: {e}")
