"""Shared serializer helpers."""
from rest_framework import serializers

from .money import format_money, mask_if_needed


class MoneyField(serializers.Field):
    """Serialises a Decimal as the design's display string, masked when needed.

    ``area``/``minimum`` describe the permission required to see the number.
    """

    def __init__(self, area="financials", minimum="restricted", **kwargs):
        self.area = area
        self.minimum = minimum
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        user = getattr(self.context.get("request"), "user", None)
        return mask_if_needed(user, format_money(value), self.area, self.minimum)

    def to_internal_value(self, data):
        return data


class BaseRecordSerializer(serializers.ModelSerializer):
    """Adds the display fields every record list in the design shows."""

    class Meta:
        abstract = True

    def actor(self):
        return getattr(self.context.get("request"), "user", None)
