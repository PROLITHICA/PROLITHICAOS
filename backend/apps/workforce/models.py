from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

class DailyLog(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey("delivery.Project", on_delete=models.PROTECT)
    date = models.DateField()
    minutes = models.PositiveIntegerField()
    summary = models.TextField(max_length=4000)
    class Meta:
        ordering = ["-date", "-created_at"]

class Thread(BaseModel):
    name = models.CharField(max_length=120, blank=True)
    direct_key = models.CharField(max_length=80, unique=True, null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="chat_threads")

class Message(BaseModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField(max_length=4000)
    class Meta:
        ordering = ["created_at", "id"]
