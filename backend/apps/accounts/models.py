"""People, roles, permissions and the audit trail."""
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel

LEVELS = ["none", "read", "contribute", "restricted", "full", "approve", "administer"]
LEVEL_RANK = {name: index for index, name in enumerate(LEVELS)}

AREAS = [
    ("company_performance", "Company performance, pipeline, cash and risk"),
    ("project_financials", "All project financials and margins"),
    ("financials", "Financial detail"),
    ("finance", "Invoices, payments, expenses and profitability"),
    ("contracts", "Contracts, proposals and amendments"),
    ("org_contracts", "Organisation and contract records"),
    ("client_commercial", "Client commercial history"),
    ("client_contacts", "Client contacts"),
    ("delivery", "Project delivery detail"),
    ("assigned_projects", "Assigned projects, requirements and tasks"),
    ("requirements", "Requirements and knowledge base"),
    ("research", "Discovery, research and prototypes"),
    ("technical_docs", "Technical documentation and architecture"),
    ("support", "Support incidents and SLAs"),
    ("correspondence", "Correspondence, minutes and documents"),
    ("meetings", "Meetings, signatures and reminders"),
    ("user_admin", "Users, roles and permission grants"),
    ("audit", "Audit trail"),
]


class Department(BaseModel):
    """One of the five departments in the design's sidebar."""

    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=60)
    initials = models.CharField(max_length=4)
    home_view = models.CharField(max_length=40, default="command")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label


class Role(BaseModel):
    SCOPE = [
        ("company", "Company"),
        ("assigned_projects", "Assigned projects"),
        ("own_records", "Own records only"),
    ]
    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=60)
    scope = models.CharField(max_length=20, choices=SCOPE, default="assigned_projects")
    mfa_required = models.BooleanField(default=True)
    is_director = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label

    def level_for(self, area):
        if self.is_director:
            return "administer"
        grant = self.permissions.filter(area=area).first()
        return grant.level if grant else "none"


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    area = models.CharField(max_length=40, choices=AREAS)
    level = models.CharField(max_length=16, choices=[(x, x) for x in LEVELS], default="none")

    class Meta:
        unique_together = ("role", "area")
        ordering = ["area"]

    def __str__(self):
        return f"{self.role.slug}:{self.area}={self.level}"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("An email address is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    STATE = [
        ("active", "Active"),
        ("onboarding", "Onboarding"),
        ("invited", "Invited"),
        ("over_capacity", "Over capacity"),
        ("suspended", "Suspended"),
    ]
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80)
    job_title = models.CharField(max_length=80, blank=True)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="members"
    )
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    state = models.CharField(max_length=20, choices=STATE, default="active")
    utilisation = models.PositiveSmallIntegerField(null=True, blank=True)
    mfa_enabled = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    last_sign_in = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name or self.email

    @property
    def initials(self):
        parts = [p for p in (self.display_name or self.email).split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return (parts[0][:2] if parts else "??").upper()

    @property
    def first_name_only(self):
        return (self.display_name or self.email).split(" ")[0]

    @property
    def scope(self):
        if self.is_superuser or (self.role and self.role.is_director):
            return "company"
        return self.role.scope if self.role else "own_records"

    def level_for(self, area):
        if self.is_superuser or (self.role and self.role.is_director):
            return "administer"
        return self.role.level_for(area) if self.role else "none"

    def permission_map(self):
        return {area: self.level_for(area) for area, _ in AREAS}


class Person(BaseModel):
    """Directory row for the People register (may or may not have an account)."""

    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="person"
    )
    name = models.CharField(max_length=80)
    role_label = models.CharField(max_length=60)
    department_label = models.CharField(max_length=60)
    projects_label = models.CharField(max_length=80, blank=True)
    utilisation_label = models.CharField(max_length=12, default="—")
    permissions_label = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=30, default="Active")
    tag_class = models.CharField(max_length=20, default="tag-accent")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class UserSession(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    key = models.CharField(max_length=40)
    device = models.CharField(max_length=80)
    location = models.CharField(max_length=80, blank=True)
    last_active = models.CharField(max_length=60, blank=True)
    current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-current", "-created_at"]

    def __str__(self):
        return f"{self.user}: {self.device}"


class Delegation(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="delegation")
    delegate_to = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="delegated_from"
    )
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} → {self.delegate_to}"


class NotificationPreference(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    email = models.BooleanField(default=True)
    digest = models.BooleanField(default=True)
    mobile = models.BooleanField(default=False)
    mentions = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user}"


class AuditEvent(BaseModel):
    """Append-only. Read-only for everyone, including administrators."""

    CLASSES = [
        ("routine", "Routine"),
        ("financial", "Financial"),
        ("sensitive", "Sensitive"),
    ]
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    actor_name = models.CharField(max_length=80, blank=True)
    action = models.CharField(max_length=120)
    record_ref = models.CharField(max_length=60, blank=True)
    detail = models.CharField(max_length=200, blank=True)
    event_class = models.CharField(max_length=12, choices=CLASSES, default="routine")
    when_label = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor_name}: {self.action}"

    @property
    def tag_class(self):
        return {
            "sensitive": "tag-accent-2",
            "financial": "tag-outline",
            "routine": "tag-neutral",
        }[self.event_class]
