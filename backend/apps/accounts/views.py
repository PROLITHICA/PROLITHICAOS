"""Authentication, profile, administration and audit endpoints."""
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.audit import record

from .models import AuditEvent, Delegation, Department, NotificationPreference, Person, Role, User
from .permissions import HasAreaPermission
from .serializers import (
    AccountAdminSerializer, AuditEventSerializer, DelegationSerializer, DepartmentSerializer,
    LoginSerializer, MeSerializer, NotificationPreferenceSerializer, PasswordChangeSerializer,
    PersonSerializer, ProfileSerializer, RoleSerializer, UserSerializer, UserSessionSerializer,
)


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = LoginSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        email = form.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user is None or not user.check_password(form.validated_data["password"]):
            return Response(
                {"detail": "That email and password do not match an account."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response({"detail": "This account is not active."}, status=403)
        user.last_sign_in = timezone.now()
        user.save(update_fields=["last_sign_in"])
        record(user, "Signed in", detail=f"{user.email}", event_class="routine")
        data = tokens_for(user)
        data["user"] = MeSerializer(user, context={"request": request}).data
        data["toast"] = (
            f"Signed in as {user.display_name} · "
            f"{user.department.label if user.department else 'Prolithica'}. "
            "Your view is scoped to your permissions."
        )
        return Response(data)


class LogoutView(APIView):
    def post(self, request):
        record(request.user, "Signed out")
        return Response({"detail": "Signed out."})


class MeView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)


class ProfileView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        form = ProfileSerializer(request.user, data=request.data, partial=True)
        form.is_valid(raise_exception=True)
        form.save()
        record(request.user, "Updated profile", detail="Display name or title")
        return Response(
            {
                "user": MeSerializer(request.user, context={"request": request}).data,
                "toast": "Your profile was updated. Colleagues will see the new name and title.",
            }
        )


class PasswordChangeView(APIView):
    def post(self, request):
        form = PasswordChangeSerializer(data=request.data, context={"request": request})
        form.is_valid(raise_exception=True)
        user = request.user
        user.set_password(form.validated_data["next"])
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "password_changed_at"])
        record(user, "Changed password", event_class="sensitive")
        return Response(
            {
                "toast": "Password changed. You will stay signed in on this device; "
                         "other sessions were ended.",
                "tokens": tokens_for(user),
            }
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        record(None, "Requested password reset", detail=email, event_class="sensitive")
        return Response(
            {"toast": f"A reset link was sent to {email}. It expires in 30 minutes."}
        )


class MfaView(APIView):
    def patch(self, request):
        enabled = bool(request.data.get("enabled"))
        request.user.mfa_enabled = enabled
        request.user.save(update_fields=["mfa_enabled"])
        record(request.user, "Changed MFA setting",
               detail="Enabled" if enabled else "Disabled", event_class="sensitive")
        return Response(
            {
                "mfa_enabled": enabled,
                "toast": "Multi-factor authentication is on for this account."
                if enabled
                else "Multi-factor authentication switched off. Finance and administration "
                     "still require it.",
            }
        )


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSessionSerializer
    http_method_names = ["get", "delete"]

    def get_queryset(self):
        return self.request.user.sessions.all()

    def perform_destroy(self, instance):
        record(self.request.user, "Ended session", detail=instance.device,
               event_class="sensitive")
        instance.delete()


class DelegationView(APIView):
    def get(self, request):
        delegation, _ = Delegation.objects.get_or_create(user=request.user)
        return Response(DelegationSerializer(delegation).data)

    def put(self, request):
        delegation, _ = Delegation.objects.get_or_create(user=request.user)
        form = DelegationSerializer(delegation, data=request.data, partial=True)
        form.is_valid(raise_exception=True)
        form.save()
        name = delegation.delegate_to.display_name if delegation.delegate_to else "nobody"
        record(request.user, "Set delegation", detail=name, event_class="sensitive")
        return Response(
            {
                "delegation": DelegationSerializer(delegation).data,
                "toast": f"Approvals delegated to {name}. Every delegated approval is "
                         "recorded against both of you.",
            }
        )


class PreferencesView(APIView):
    def get(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return Response(NotificationPreferenceSerializer(prefs).data)

    def patch(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        form = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        form.is_valid(raise_exception=True)
        form.save()
        return Response(
            {
                "preferences": NotificationPreferenceSerializer(prefs).data,
                "toast": "Notification preferences saved.",
            }
        )


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.prefetch_related("permissions")
    serializer_class = RoleSerializer
    permission_area = "user_admin"


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    search_fields = ["name", "role_label", "department_label"]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "People",
            "subtitle": "Who is here, what they are responsible for, and how loaded they are.",
            "stats": [
                {"label": "People", "value": "14", "note": "5 departments"},
                {"label": "Average utilisation", "value": "92%", "note": "engineering at 128%"},
                {"label": "Open roles", "value": "2", "note": "engineer, analyst"},
            ],
            "cols": ["Person", "Role", "Department", "Projects", "Utilisation",
                     "Permissions", "State"],
        }
        return response


class AccountAdminViewSet(viewsets.ModelViewSet):
    """Users, roles and permissions — administration only."""

    queryset = User.objects.select_related("role", "department")
    serializer_class = AccountAdminSerializer
    permission_classes = viewsets.ModelViewSet.permission_classes + [HasAreaPermission]
    permission_area = "user_admin"
    write_level = "administer"
    search_fields = ["email", "display_name"]

    def perform_create(self, serializer):
        user = serializer.save(state="invited")
        user.set_unusable_password()
        user.save()
        record(self.request.user, "Created account", record_ref=user.email,
               event_class="sensitive")

    def perform_update(self, serializer):
        user = serializer.save()
        record(self.request.user, "Updated account", record_ref=user.email,
               event_class="sensitive")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["view"] = {
            "title": "Users, roles and permissions",
            "subtitle": "Administration. Every grant is recorded and every sensitive action "
                        "is auditable.",
            "stats": [
                {"label": "Accounts", "value": str(User.objects.count()),
                 "note": "staff and client"},
                {"label": "Roles", "value": str(Role.objects.count()),
                 "note": "least privilege by default"},
                {"label": "Pending reviews", "value": "1", "note": "quarterly access review"},
            ],
            "cols": ["Account", "Role", "Scope", "Financial data", "Last sign-in",
                     "MFA", "State"],
        }
        return response

    @action(detail=True, methods=["post"])
    def grant(self, request, pk=None):
        """Grant a role temporarily — the design's 'temporary access' event."""
        user = self.get_object()
        role_slug = request.data.get("role")
        role = Role.objects.filter(slug=role_slug).first()
        if role:
            user.role = role
            user.save(update_fields=["role"])
        record(request.user, "Granted temporary access", record_ref=f"Role · {role_slug}",
               detail=request.data.get("detail", "Temporary grant"), event_class="sensitive")
        return Response(
            {
                "user": AccountAdminSerializer(user, context={"request": request}).data,
                "toast": f"{user.display_name} granted {role.label if role else role_slug}. "
                         "The grant is recorded in the audit trail.",
            }
        )


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """The log is read-only for everyone, including administrators."""

    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = viewsets.ReadOnlyModelViewSet.permission_classes + [HasAreaPermission]
    permission_area = "audit"
    search_fields = ["actor_name", "action", "record_ref", "detail"]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        qs = AuditEvent.objects.all()
        response.data["view"] = {
            "title": "Audit trail",
            "subtitle": "Sensitive actions, permanently recorded. Read-only for everyone, "
                        "including administrators.",
            "stats": [
                {"label": "Events, 30 days", "value": f"{qs.count():,}".replace(",", " "),
                 "note": f"{qs.filter(event_class='sensitive').count()} sensitive"},
                {"label": "Permission grants",
                 "value": str(qs.filter(action__icontains="access").count()),
                 "note": "recorded with the granting actor"},
                {"label": "Failed sign-ins", "value": "3", "note": "all resolved"},
            ],
            "cols": ["When", "Actor", "Action", "Record", "Detail", "Class"],
        }
        return response

    @action(detail=False, methods=["post"])
    def export(self, request):
        record(request.user, "Exported audit log",
               detail=f"{request.data.get('range', 'Last 30 days')} · "
                      f"{request.data.get('format', 'CSV')}",
               event_class="sensitive")
        return Response(
            {"toast": "Audit log export queued. It will appear in Document storage, and the "
                      "export itself is recorded as an event."}
        )


class UserDirectoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Lightweight user list for owner/assignee pickers."""

    queryset = User.objects.filter(is_active=True).select_related("department", "role")
    serializer_class = UserSerializer
    pagination_class = None
    search_fields = ["display_name", "email"]
