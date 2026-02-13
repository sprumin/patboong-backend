from django.contrib import admin
from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "view_count", "created_at")
    list_filter = ("created_at", "author")
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("created_at", "updated_at", "view_count")
