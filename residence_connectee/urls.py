from rest_framework import routers
from .views import SmartDeviceViewSet, StudyRoomViewSet,StudyRoomReservationViewSet, NewsViewSet

router = routers.DefaultRouter()

router.register(r"smart-devices", SmartDeviceViewSet)
router.register(r'study-rooms', StudyRoomViewSet, basename='studyroom')
router.register(r"study-room-reservations", StudyRoomReservationViewSet)
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = router.urls