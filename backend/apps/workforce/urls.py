from django.urls import path
from .views import WorkspaceView, CompleteView, LogsView, ThreadsView, MessagesView, SetupView, MembershipView
urlpatterns=[path("",WorkspaceView.as_view()),path("tasks/<uuid:pk>/",CompleteView.as_view()),path("logs/",LogsView.as_view()),path("threads/",ThreadsView.as_view()),path("threads/<uuid:pk>/messages/",MessagesView.as_view()),path("setup/",SetupView.as_view()),path("memberships/",MembershipView.as_view())]
