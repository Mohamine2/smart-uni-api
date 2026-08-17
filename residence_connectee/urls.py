from rest_framework import routers
from .views import SmartDeviceViewSet, StudyRoomReservationViewSet

router = routers.DefaultRouter()

router.register(r"smart-devices", SmartDeviceViewSet)
router.register(r"study-room-reservations", StudyRoomReservationViewSet)

urlpatterns = router.urls