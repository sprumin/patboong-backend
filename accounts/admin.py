from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Friendship, MatchingRecord, MatchingRun, MatchingSettings

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "created_at")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("추가 정보", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "created_at")
    search_fields = ("user__username", "friend__username")


@admin.register(MatchingSettings)
class MatchingSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not MatchingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MatchingRun)
class MatchingRunAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("owner__username",)
    readonly_fields = ("created_at",)


@admin.register(MatchingRecord)
class MatchingRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "team_number", "balance_score", "saved_at")
    list_filter = ("saved_at",)
    search_fields = ("owner__username",)
    readonly_fields = ("saved_at",)
