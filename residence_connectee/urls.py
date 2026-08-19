from rest_framework import routers
from .views import SmartDeviceViewSet, StudyRoomReservationViewSet, NewsViewSet

router = routers.DefaultRouter()

router.register(r"smart-devices", SmartDeviceViewSet)
router.register(r"study-room-reservations", StudyRoomReservationViewSet)
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = router.urls