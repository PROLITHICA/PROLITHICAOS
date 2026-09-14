from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView as BaseAPIView
from rest_framework.permissions import IsAuthenticated, BasePermission

CLIENT_ROLE_SLUGS = ("client", "client_portal")


def is_employee(user):
    return not (user.role and user.role.slug in CLIENT_ROLE_SLUGS)


class EmployeeOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and is_employee(request.user)

class APIView(BaseAPIView):
    permission_classes = [IsAuthenticated, EmployeeOnly]
from apps.accounts.models import User, Department, Role
from apps.delivery.models import Project, ProjectMember, Task
from .models import DailyLog, Thread, Message


def ceo(user):
    return user.is_superuser or bool(user.role and user.role.is_director)


def projects(user):
    qs = Project.objects.exclude(is_archived=True).exclude(state="closed")
    if ceo(user): return qs
    criterion = Q(members__user=user) | Q(manager=user) | Q(tasks__assignee=user)
    if user.is_department_head and user.department_id:
        criterion |= Q(members__user__department_id=user.department_id) | Q(tasks__assignee__department_id=user.department_id)
    return qs.filter(criterion).distinct()


def staff(user):
    qs = User.objects.filter(is_active=True).exclude(state="suspended").exclude(role__slug__in=CLIENT_ROLE_SLUGS)
    return qs if ceo(user) else qs.filter(department_id=user.department_id) if user.is_department_head and user.department_id else qs.filter(pk=user.pk)


def task_scope(user):
    qs = Task.objects.select_related("assignee", "project")
    return qs if ceo(user) else qs.filter(assignee__in=staff(user))


class TaskForm(serializers.Serializer):
    text = serializers.CharField(max_length=200)
    assignee = serializers.UUIDField()
    project = serializers.UUIDField()


class LogForm(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        fields = ["id", "project", "date", "minutes", "summary"]
        read_only_fields = ["id"]
    def validate(self, data):
        if not projects(self.context["request"].user).filter(pk=data["project"].pk).exists():
            raise serializers.ValidationError("Choose one of your assigned projects.")
        if data["date"] > timezone.localdate(): raise serializers.ValidationError("Daily logs cannot be dated in the future.")
        if not 1 <= data["minutes"] <= 1440: raise serializers.ValidationError("Enter between 1 and 1440 minutes.")
        if not data["summary"].strip(): raise serializers.ValidationError("Describe the work you completed.")
        return data


class WorkspaceView(APIView):
    def get(self, request):
        user = request.user
        logs = DailyLog.objects.filter(user__in=staff(user)).select_related("user", "project")[:100]
        return Response({
            "can_assign": ceo(user) or user.is_department_head,
            "is_ceo": ceo(user), "employee_number": user.employee_number,
            "projects": list(projects(user).values("id", "ref", "name", "stage", "completion")),
            "people": list(staff(user).values("id", "display_name", "employee_number")),
            "tasks": [{"id":t.id, "text":t.text, "done":t.done, "project":t.project.name, "assignee":t.assignee.display_name if t.assignee else "Unassigned", "can_complete":ceo(user) or user.is_department_head or t.assignee_id==user.id} for t in task_scope(user).order_by("done", "-created_at")[:200]],
            "logs": [{"id":l.id, "date":l.date, "minutes":l.minutes, "summary":l.summary, "person":l.user.display_name, "project":l.project.name} for l in logs],
        })
    def post(self, request):
        if not (ceo(request.user) or request.user.is_department_head): raise PermissionDenied("Only the CEO or a department head can assign work.")
        form = TaskForm(data=request.data); form.is_valid(raise_exception=True)
        person = get_object_or_404(staff(request.user), pk=form.validated_data["assignee"])
        project = get_object_or_404(projects(request.user), pk=form.validated_data["project"])
        with transaction.atomic():
            task = Task.objects.create(text=form.validated_data["text"], assignee=person, project=project, created_by=request.user, project_label=project.short_label[:20])
            ProjectMember.objects.get_or_create(project=project, user=person, defaults={"role_label":"Contributor"})
        return Response({"id":task.id}, status=201)


class CompleteView(APIView):
    def patch(self, request, pk):
        task = get_object_or_404(task_scope(request.user), pk=pk)
        if not isinstance(request.data.get("done"), bool): raise serializers.ValidationError({"done":"Provide true or false."})
        task.done=request.data["done"]; task.save(update_fields=["done", "updated_at"])
        return Response({"done":task.done})


class LogsView(APIView):
    def post(self, request):
        form = LogForm(data=request.data, context={"request":request}); form.is_valid(raise_exception=True)
        form.save(user=request.user, created_by=request.user)
        return Response(form.data, status=201)


class MembershipView(APIView):
    def post(self, request):
        if not ceo(request.user): raise PermissionDenied("The CEO manages project membership.")
        form = TaskForm(data={**request.data, "text":"membership"}); form.is_valid(raise_exception=True)
        person = get_object_or_404(staff(request.user), pk=form.validated_data["assignee"])
        project = get_object_or_404(projects(request.user), pk=form.validated_data["project"])
        ProjectMember.objects.get_or_create(project=project,user=person,defaults={"role_label":"Contributor"})
        return Response({"detail":"Project membership saved."})


class SetupView(APIView):
    def get(self, request):
        if not ceo(request.user): raise PermissionDenied()
        return Response({"departments":list(Department.objects.values("id","label")), "roles":list(Role.objects.values("id","label"))})


def group_admins():
    return User.objects.filter(is_active=True).filter(Q(is_superuser=True)|Q(role__is_director=True))


def visible_threads(user):
    # CEOs are members/admins of every group, including groups predating their appointment.
    return Thread.objects.filter(Q(members=user) | Q(direct_key__isnull=True) if ceo(user) else Q(members=user)).distinct()


class ThreadForm(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, default="")
    members = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=100)
    direct = serializers.BooleanField(default=False)
    def validate(self, data):
        ids=set(data["members"]); ids.discard(self.context["request"].user.id)
        if not ids or User.objects.filter(pk__in=ids, is_active=True).exclude(state="suspended").exclude(role__slug__in=CLIENT_ROLE_SLUGS).count()!=len(ids):
            raise serializers.ValidationError("Choose active employees.")
        if data["direct"] and len(ids)!=1: raise serializers.ValidationError("A private conversation has two participants.")
        if not data["direct"] and not data["name"].strip(): raise serializers.ValidationError("Give the group a name.")
        data["members"]=ids
        return data


class ThreadsView(APIView):
    def get(self, request):
        rows=[]
        for thread in visible_threads(request.user).prefetch_related("members").order_by("-updated_at"):
            members=list(thread.members.all())
            if thread.direct_key is None:
                members=list({u.pk:u for u in members+list(group_admins())}.values())
            rows.append({"id":thread.id,"name":thread.name if not thread.direct_key else ", ".join(u.display_name for u in members if u.pk!=request.user.pk),"direct":bool(thread.direct_key),"can_manage":bool(not thread.direct_key and ceo(request.user)),"members":[{"id":u.id,"name":u.display_name,"admin":bool(not thread.direct_key and ceo(u))} for u in members]})
        directory=User.objects.filter(is_active=True).exclude(pk=request.user.pk).exclude(state="suspended").exclude(role__slug__in=CLIENT_ROLE_SLUGS)
        return Response({"threads":rows,"people":list(directory.values("id","display_name","employee_number"))})
    def post(self, request):
        form=ThreadForm(data=request.data,context={"request":request}); form.is_valid(raise_exception=True)
        data=form.validated_data
        with transaction.atomic():
            if data["direct"]:
                key=":".join(sorted([str(request.user.id), str(next(iter(data["members"]))) ]))
                thread,_=Thread.objects.get_or_create(direct_key=key,defaults={"created_by":request.user})
            else: thread=Thread.objects.create(name=data["name"],created_by=request.user)
            thread.members.add(request.user,*data["members"])
            if not data["direct"]: thread.members.add(*group_admins())
        return Response({"id":thread.id},status=201)


class MessageForm(serializers.Serializer):
    body=serializers.CharField(max_length=4000)


class MessagesView(APIView):
    def get(self, request, pk):
        thread=get_object_or_404(visible_threads(request.user),pk=pk)
        messages=list(thread.messages.select_related("author").order_by("-created_at","-id")[:200]); messages.reverse()
        return Response([{"id":m.id,"body":m.body,"author":m.author.display_name,"created_at":m.created_at,"mine":m.author_id==request.user.id} for m in messages])
    def post(self, request, pk):
        thread=get_object_or_404(visible_threads(request.user),pk=pk)
        form=MessageForm(data=request.data);form.is_valid(raise_exception=True)
        message=Message.objects.create(thread=thread,author=request.user,body=form.validated_data["body"],created_by=request.user)
        thread.save(update_fields=["updated_at"])
        return Response({"id":message.id},status=201)
    def patch(self, request, pk):
        thread=get_object_or_404(visible_threads(request.user),pk=pk)
        if thread.direct_key or not ceo(request.user): raise PermissionDenied("Only the CEO can manage company groups.")
        form=ThreadForm(data={"name":request.data.get("name",thread.name),"members":request.data.get("members",[]),"direct":False},context={"request":request})
        form.is_valid(raise_exception=True)
        with transaction.atomic():
            thread.name=form.validated_data["name"]
            thread.save(update_fields=["name","updated_at"])
            thread.members.set([request.user,*form.validated_data["members"],*group_admins()])
        return Response({"detail":"Group membership updated."})

    def delete(self, request, pk):
        thread=get_object_or_404(visible_threads(request.user),pk=pk)
        if thread.direct_key or not ceo(request.user): raise PermissionDenied("Only the CEO can close a company group.")
        thread.delete()
        return Response(status=204)
