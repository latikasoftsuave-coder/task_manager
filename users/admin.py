# users/admin.py
from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('id',)
