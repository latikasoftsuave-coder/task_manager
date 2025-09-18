from django.urls import path
from . import views

urlpatterns = [
    path('', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('<uuid:id>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('<uuid:task_id>/add-category/', views.add_category_to_task, name='add-category'),
    path('<uuid:task_id>/add-tag/', views.add_tag_to_task, name='add-tag'),
    path('<uuid:task_id>/logs/', views.task_logs, name='task-logs'),
    path('reminders/', views.get_reminders, name='get-reminders'),
    path('filter/', views.filter_tasks, name='filter-tasks'),
]
