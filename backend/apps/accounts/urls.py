from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("sessions", views.SessionViewSet, basename="session")

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path("mfa/", views.MfaView.as_view(), name="mfa"),
    path("delegation/", views.DelegationView.as_view(), name="delegation"),
    path("preferences/", views.PreferencesView.as_view(), name="preferences"),
    path("", include(router.urls)),
]
