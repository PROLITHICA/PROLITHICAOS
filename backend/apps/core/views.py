"""Cross-app endpoints: the Command Centre, notifications, search and Ask Prolithica."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasAreaPermission, user_has_level

from .dashboard import command_centre, take_decision
from .intelligence import answer, suggestions
from .models import Notification
from .search import search
from .serializers_notifications import NotificationSerializer

# The three notification groups the design renders, in order.
GROUPS = [
    ("Critical", "tag-accent-2", ["approval", "risk", "finance"], 600),
    ("Actionable", "tag-outline", ["delivery", "mention"], 500),
    ("Informational", "tag-neutral", ["system"], 400),
]


class CommandCentreView(APIView):
    permission_classes = APIView.permission_classes + [HasAreaPermission]
    permission_area = "company_performance"

    def get(self, request):
        return Response(command_centre(request.user))

    def post(self, request):
        """Act on one of the decisions waiting on the executive."""
        if not user_has_level(request.user, "contracts", "approve"):
            raise PermissionDenied("Only an approver may act on these decisions.")
        return Response(take_decision(request.data.get("action", ""), request.user))


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    http_method_names = ["get", "patch", "post", "delete"]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        rows = list(self.get_queryset())
        groups = []
        for heading, tag_class, kinds, weight in GROUPS:
            items = [
                {
                    "id": str(row.id),
                    "text": row.title,
                    "meta": row.body,
                    "cta": "Open",
                    "route": row.route,
                    "weight": weight if not row.read else 400,
                    "read": row.read,
                }
                for row in rows
                if row.kind in kinds
            ]
            if items:
                groups.append(
                    {
                        "heading": heading,
                        "tag_class": tag_class,
                        "count": str(len(items)),
                        "items": items,
                    }
                )
        return Response(
            {
                "title": "Notifications",
                "subtitle": "Meaningful events only. Each one says whether it is critical, "
                            "actionable or informational.",
                "unread": sum(1 for row in rows if not row.read),
                "groups": groups,
            }
        )

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().update(read=True)
        return Response(
            {
                "toast": "All notifications marked read. Critical items stay on the Command "
                         "Centre until they are resolved."
            }
        )

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        row = self.get_object()
        row.read = True
        row.save(update_fields=["read"])
        return Response({"notification": NotificationSerializer(row).data})


class SearchView(APIView):
    def get(self, request):
        return Response(search(request.query_params.get("q", "").strip(), request.user))


class IntelligenceView(APIView):
    def get(self, request):
        return Response(
            {
                "title": "Ask Prolithica",
                "subtitle": "Questions answered from the company's own records, inside your "
                            "permissions. Answers cite the records they came from.",
                "suggestions": suggestions(),
                **answer(None, request.user),
            }
        )

    def post(self, request):
        result = answer(request.data.get("question", ""), request.user)
        result["suggestions"] = suggestions()
        return Response(result)
