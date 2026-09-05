from rest_framework.routers import DefaultRouter
from apps.locations.views import CategoryViewSet, LocationViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = router.urls
