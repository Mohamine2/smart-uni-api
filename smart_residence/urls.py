from rest_framework import routers
from .views import SmartDeviceViewSet, StudyRoomViewSet, StudyRoomReservationViewSet, NewsViewSet, ApartmentViewSet, \
    RoomViewSet, StudentViewSet

router = routers.DefaultRouter()

router.register(r'students', StudentViewSet, basename='student')
router.register(r'apartments', ApartmentViewSet, basename='apartment')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r"smart-devices", SmartDeviceViewSet)
router.register(r'study-rooms', StudyRoomViewSet, basename='studyroom')
router.register(r"study-room-reservations", StudyRoomReservationViewSet)
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = router.urls