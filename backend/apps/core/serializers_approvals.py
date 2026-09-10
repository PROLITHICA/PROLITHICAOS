from rest_framework import serializers

from .models import ApprovalRequest


class ApprovalSerializer(serializers.ModelSerializer):
    tag_class = serializers.CharField(read_only=True)
    state_label = serializers.CharField(source="get_state_display", read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id", "title", "detail", "kind", "kind_label", "amount", "waiting_label",
            "requested_by_name", "cta", "route", "state", "state_label", "tag_class",
            "outcome", "decided_at", "target_ref",
        ]
        read_only_fields = ["state", "outcome", "decided_at"]
