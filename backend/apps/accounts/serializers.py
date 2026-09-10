"""Serializers for identity, permissions, profile and the audit trail."""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    AREAS, AuditEvent, Delegation, Department, NotificationPreference, Person, Role,
    RolePermission, User, UserSession,
)
from .navigation import nav_for, visible_departments


class DepartmentSerializer(serializers.ModelSerializer):
    head = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "slug", "label", "initials", "home_view", "order", "head"]

    def get_head(self, obj):
        member = obj.members.order_by("created_at").first()
        return {"name": member.display_name, "title": member.job_title} if member else None


class RolePermissionSerializer(serializers.ModelSerializer):
    area_label = serializers.SerializerMethodField()

    class Meta:
        model = RolePermission
        fields = ["id", "area", "area_label", "level"]

    def get_area_label(self, obj):
        return dict(AREAS).get(obj.area, obj.area)


class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ["id", "slug", "label", "scope", "mfa_required", "is_director", "permissions"]


class UserSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    initials = serializers.CharField(read_only=True)
    first_name_only = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "display_name", "job_title", "initials", "first_name_only",
            "department", "role", "state", "utilisation", "mfa_enabled", "last_sign_in",
            "password_changed_at",
        ]


class MeSerializer(UserSerializer):
    """Everything the shell needs on boot: identity, permissions, navigation."""

    permissions = serializers.SerializerMethodField()
    scope = serializers.CharField(read_only=True)
    nav_groups = serializers.SerializerMethodField()
    permission_rows = serializers.SerializerMethodField()
    home_view = serializers.SerializerMethodField()
    visible_departments = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "permissions", "scope", "nav_groups", "permission_rows", "home_view", "visible_departments",
        ]

    def get_permissions(self, obj):
        return obj.permission_map()

    def get_nav_groups(self, obj):
        return nav_for(obj)

    def get_permission_rows(self, obj):
        """The 'My permissions' tab: area label + granted level, in role order."""
        if not obj.role:
            return []
        return [
            {"area": dict(AREAS).get(p.area, p.area), "level": p.level.replace("_", " ").title()}
            for p in obj.role.permissions.all()
        ]

    def get_home_view(self, obj):
        return "dashboard"

    def get_visible_departments(self, obj):
        return DepartmentSerializer(visible_departments(obj), many=True).data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    current = serializers.CharField()
    next = serializers.CharField()
    confirm = serializers.CharField()

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current"]):
            raise serializers.ValidationError({"current": "That is not your current password."})
        if attrs["next"] != attrs["confirm"]:
            raise serializers.ValidationError({"confirm": "The two passwords do not match."})
        validate_password(attrs["next"], user)
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["display_name", "job_title"]


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ["id", "device", "location", "last_active", "current"]


class DelegationSerializer(serializers.ModelSerializer):
    delegate_to_name = serializers.CharField(source="delegate_to.display_name", read_only=True)

    class Meta:
        model = Delegation
        fields = ["id", "delegate_to", "delegate_to_name", "starts_on", "ends_on", "note", "active"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["email", "digest", "mobile", "mentions"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "id", "name", "role_label", "department_label", "projects_label",
            "utilisation_label", "permissions_label", "state", "tag_class",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    tag_class = serializers.CharField(read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id", "when_label", "actor_name", "action", "record_ref", "detail",
            "event_class", "tag_class", "created_at",
        ]


class AccountAdminSerializer(serializers.ModelSerializer):
    """The 'Users, roles and permissions' administration table."""

    role_label = serializers.CharField(source="role.label", read_only=True)
    scope_label = serializers.SerializerMethodField()
    financial_data = serializers.SerializerMethodField()
    last_sign_in_label = serializers.SerializerMethodField()
    mfa_label = serializers.SerializerMethodField()
    state_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "display_name", "role", "role_label", "scope_label",
            "financial_data", "last_sign_in_label", "mfa_label", "state_label",
            "state", "mfa_enabled",
        ]

    def get_scope_label(self, obj):
        return dict(Role.SCOPE).get(obj.scope, obj.scope)

    def get_financial_data(self, obj):
        level = obj.level_for("financials")
        if level in ("full", "approve", "administer"):
            return "Full"
        if level == "restricted":
            return "Restricted"
        return "None"

    def get_last_sign_in_label(self, obj):
        return obj.last_sign_in.strftime("%-d %b, %H:%M") if obj.last_sign_in else "Never"

    def get_mfa_label(self, obj):
        return "Enabled" if obj.mfa_enabled else "Pending"

    def get_state_label(self, obj):
        return obj.get_state_display()
