from django.urls import path
from .views import RegisterView, CustomLoginView, profile_view

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="token_obtain_pair"),
    path("profile/", profile_view, name="profile"),
]
