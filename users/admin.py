from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import ModelForm
from .models import User

# User creation form
class UserCreationForm(ModelForm):
    class Meta:
        model = User
        fields = ("email", "password")

# User change form
class UserChangeForm(ModelForm):
    class Meta:
        model = User
        fields = ("email", "password", "is_active", "is_staff", "is_superuser")

# Custom UserAdmin
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")  # remove groups & permissions

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()  # must be empty, remove groups/user_permissions

admin.site.register(User, UserAdmin)
