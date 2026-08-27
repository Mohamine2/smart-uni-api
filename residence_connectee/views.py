from django.db.models import Sum, Q, F, Avg
from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Student, News, SmartDevice, Room, StudyRoom, StudyRoomReservation, Apartment
from .permissions import IsAdminOrReadOnly, HasDeviceLevelPermission
from .serializers import SmartDeviceSerializer, StudyRoomReservationSerializer, NewsSerializer, StudyRoomSerializer, \
    RoomSerializer, ApartmentSerializer, StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):
    """
    User profile management.
    - Regular students can only access their own profile.
    - Staff members can view and manage all students.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Student.objects.all()
        return Student.objects.filter(pk=self.request.user.pk)

    def get_permissions(self):
        """Allow unauthenticated users to register (POST). Everything else requires auth."""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        """Endpoint of convenience for the frontend to access /api/students/me/"""
        student = request.user

        if request.method == 'GET':
            serializer = self.get_serializer(student)
            return Response(serializer.data)

        # Handling PATCH / PUT
        serializer = self.get_serializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def level_up(self, request):
        """Allows the student to claim the next gamification level based on total points."""
        user = request.user
        points = user.total_points

        if user.level == Student.Level.BEGINNER and points >= 3:
            user.level = Student.Level.INTERMEDIATE
            user.save(update_fields=['level'])
            return Response({"message": "Level up! You are now Intermediate."}, status=status.HTTP_200_OK)

        elif user.level == Student.Level.INTERMEDIATE and points >= 5:
            user.level = Student.Level.ADVANCED
            user.save(update_fields=['level'])
            return Response({"message": "Level up! You are now Advanced."}, status=status.HTTP_200_OK)

        elif user.level == Student.Level.ADVANCED and points >= 7:
            # Assuming you add EXPERT = 4 in your IntegerChoices
            user.level = 4
            user.save(update_fields=['level'])
            return Response({"message": "Level up! You are now an Expert."}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Not enough points to level up, or max level already reached."},
            status=status.HTTP_400_BAD_REQUEST
        )

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'apartment']
    search_fields = ['name']
    ordering_fields = ['name']

    def get_queryset(self):
        return Room.objects.filter(
            apartment__occupant=self.request.user
        ).select_related('apartment')

class ApartmentViewSet(viewsets.ModelViewSet):
    serializer_class = ApartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['apartment_number']
    search_fields = ['address', 'apartment_number']
    ordering_fields = ['apartment_number']

    def get_queryset(self):
        return Apartment.objects.filter(
            occupant=self.request.user
        ).prefetch_related('rooms')

    def perform_create(self, serializer):
        serializer.save(occupant=self.request.user)

class SmartDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = SmartDeviceSerializer
    queryset = SmartDevice.objects.select_related('room')
    permission_classes = [HasDeviceLevelPermission]

    # Standard DRF Filtering (Swagger documented automatically)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device_type', 'is_on', 'room', 'is_on']
    search_fields = ['name']
    ordering_fields = ['name', 'power_consumption']

    def get_queryset(self):
        """Strict isolation: users only see devices in their own apartment."""
        return self.queryset.filter(room__apartment__occupant=self.request.user)

    def _award_points(self):
        """Helper method to atomically increment browsing points."""
        type(self.request.user).objects.filter(pk=self.request.user.pk).update(
            browsing_points=F('browsing_points') + Decimal('0.50')
        )

    def perform_create(self, serializer):
        # Enforce defaults on creation
        serializer.save(is_on=False, power_consumption=0.0)
        self._award_points()

    def perform_update(self, serializer):
        serializer.save()
        self._award_points()

    def perform_destroy(self, instance):
        instance.delete()
        self._award_points()

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Aggregate statistics for all devices in the student's apartment."""
        user_devices = self.get_queryset()

        stats = user_devices.aggregate(
            total_consumption=Sum('power_consumption'),
            average_consumption=Avg('power_consumption')
        )

        return Response({
            'total_devices': user_devices.count(),
            'active_devices': user_devices.filter(is_on=True).count(),
            'total_power_consumption': stats['total_consumption'] or 0.0,
            'average_power_consumption': stats['average_consumption'] or 0.0,
        }, status=status.HTTP_200_OK)

class StudyRoomViewSet(viewsets.ModelViewSet):
    queryset = StudyRoom.objects.all()
    serializer_class = StudyRoomSerializer
    permission_classes=[IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        'capacity': ['exact', 'gte', 'lte'],
    }
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'capacity']
    ordering = ['name']


class StudyRoomReservationViewSet(viewsets.ModelViewSet):
    serializer_class = StudyRoomReservationSerializer
    queryset = StudyRoomReservation.objects.select_related('study_room', 'student').all()

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

        type(self.request.user).objects.filter(pk=self.request.user.pk).update(
            browsing_points=F('browsing_points') + Decimal('0.50')
        )

class NewsViewSet(viewsets.ModelViewSet):
    serializer_class = NewsSerializer
    queryset = News.objects.all()

    permission_classes = [IsAdminOrReadOnly]

    # Enable the three standard filtering mechanisms:
    # - DjangoFilterBackend: exact field filtering
    # - SearchFilter: text-based search
    # - OrderingFilter: sorting results
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    # 1. Exact filtering by category:
    filterset_fields = ['category']

    # 2. Case-insensitive text search in the title and content:
    search_fields = ['title', 'content']

    # 3. Allow clients to sort by publication date:
    ordering_fields = ['publication_date']

    # Sort by publication date in descending order by default.
    ordering = ['-publication_date']

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)

        if request.user.is_authenticated:
            type(request.user).objects.filter(pk=request.user.pk).update(
                browsing_points=F('browsing_points') + Decimal('0.50')
            )

        return response