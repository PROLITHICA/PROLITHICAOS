from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("meetings", views.MeetingViewSet, basename="meeting")
router.register("signatures", views.SignatureRequestViewSet, basename="signature")
router.register("correspondence", views.CorrespondenceViewSet, basename="correspondence")
router.register("reminders", views.ReminderViewSet, basename="reminder")
router.register("schedule", views.ScheduleItemViewSet, basename="schedule")
router.register("reports", views.ReportViewSet, basename="report")

urlpatterns = router.urls
