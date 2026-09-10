"""A write serializer built from the model itself.

The register screens read through serializers shaped for the design's tables,
which deliberately leave out most columns. Creating and editing needs the
opposite: every field a person could reasonably set. Rather than hand-writing a
second serializer per model, this builds one from the model's own fields.
"""
from django.db import models
from rest_framework import serializers

# Never writable from a form.
SKIP = {"id", "created_at", "updated_at", "created_by", "order"}


def writable_fields(model):
    """Concrete, editable fields on ``model``, in declaration order."""
    names = []
    for field in model._meta.get_fields():
        if not getattr(field, "concrete", False) or field.auto_created:
            continue
        if field.name in SKIP or isinstance(field, models.ManyToManyField):
            continue
        names.append(field.name)
    return names


def write_serializer_for(model, optional=("ref",)):
    """A ModelSerializer covering everything worth setting on ``model``."""

    class Meta:
        pass

    Meta.model = model
    Meta.fields = ["id"] + writable_fields(model)

    # Fields the record fills in as it matures may be left out of a form, but a
    # field the database genuinely requires stays required so a form that omits
    # it is told so, rather than failing at the database.
    Meta.extra_kwargs = {}
    for field in model._meta.get_fields():
        if not getattr(field, "concrete", False) or field.name not in Meta.fields:
            continue
        if field.null or getattr(field, "blank", False) or field.has_default():
            Meta.extra_kwargs[field.name] = {"required": False}
    for name in optional:
        Meta.extra_kwargs.setdefault(name, {})["required"] = False

    return type(
        f"{model.__name__}WriteSerializer",
        (serializers.ModelSerializer,),
        {"Meta": Meta},
    )
