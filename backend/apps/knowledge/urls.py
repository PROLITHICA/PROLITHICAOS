from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("research", views.ResearchThreadViewSet, basename="research-thread")
router.register("prototypes", views.PrototypeViewSet, basename="prototype")
router.register("patterns", views.PatternViewSet, basename="pattern")
router.register("lessons", views.LessonViewSet, basename="lesson")
router.register("knowledge", views.KnowledgeArticleViewSet, basename="knowledge-article")

urlpatterns = router.urls
