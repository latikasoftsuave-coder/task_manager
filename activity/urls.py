from rest_framework.routers import DefaultRouter
from .views import ActivityLogViewSet

router = DefaultRouter()
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-logs')
urlpatterns = router.urls
