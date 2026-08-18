from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AuditEvent, Delegation, Department, NotificationPreference, Person, Role, RolePermission,
    User, UserSession,
)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "scope", "is_director")
    inlines = [RolePermissionInline]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("display_name",)
    list_display = ("display_name", "email", "role", "department", "state")
    list_filter = ("role", "department", "state")
    search_fields = ("display_name", "email")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identity", {"fields": ("display_name", "job_title", "department", "role")}),
        ("Status", {"fields": ("state", "utilisation", "mfa_enabled", "last_sign_in")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "display_name", "password1", "password2")}),
    )


admin.site.register([Department, Person, UserSession, Delegation, NotificationPreference])


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_name", "action", "record_ref", "event_class")
    list_filter = ("event_class",)
    search_fields = ("actor_name", "action", "record_ref", "detail")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
