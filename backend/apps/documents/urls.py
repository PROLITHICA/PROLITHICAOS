from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("folders", views.FolderViewSet, basename="folder")
router.register("documents", views.DocumentViewSet, basename="document")
router.register("document-versions", views.DocumentVersionViewSet,
                basename="document-version")
router.register("exports", views.ExportJobViewSet, basename="export")

urlpatterns = router.urls
