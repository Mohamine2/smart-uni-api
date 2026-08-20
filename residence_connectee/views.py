from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.db.models import Sum, Q, F, Avg
from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action

from . import permissions
from .models import Student, News, SmartDevice, Room, StudyRoom, StudyRoomReservation, Apartment
from .forms import StudentRegistrationForm, SmartDeviceForm, RenameDeviceForm, ManageDeviceForm, ProfileEditForm, \
    RoomReservationForm
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


# --- 1. HOME & NEWS MODULE ---

def home_view(request):
    category = request.GET.get('category', '')
    q_news = request.GET.get('q_news', '')
    cat_filter = request.GET.get('category', '')
    order = request.GET.get('order', '-publication_date')

    news_list = News.objects.all()

    if q_news:
        news_list = news_list.filter(Q(title__icontains=q_news) | Q(content__icontains=q_news))

    if cat_filter:
        news_list = news_list.filter(category=cat_filter)

    if order in ['publication_date', '-publication_date']:
        news_list = news_list.order_by(order)
    else:
        news_list = news_list.order_by('-publication_date')

    # --- GAMIFICATION ---
    if request.user.is_authenticated and (q_news or cat_filter):
        request.user.browsing_points += Decimal('0.50')
        request.user.save()

    context = {
        'news_list': news_list,
        'categories': News.CATEGORY_CHOICES,
        'selected_cat': category,
        'selected_order': order,
        'rooms': Room.objects.all(),
        'type_choices': SmartDevice.TYPE_CHOICES,
    }

    return render(request, 'index.html', context)

# --- 2. AUTHENTICATION MODULE ---

def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save() # Le mot de passe est haché et sauvegardé automatiquement
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Error during registration. Please check the fields.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'student': request.user})

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        # Pre-fills the form with the user's current information
        form = ProfileEditForm(instance=user)

    # N'oubliez pas de passer 'form' au contexte !
    return render(request, 'edit_profile.html', {'form': form, 'user': user})

@login_required
def student_list(request):
    students = Student.objects.filter(is_superuser=False, is_active=True).order_by('last_name', 'first_name')
    return render(request, 'student_list.html', {'students': students})


# Level Requirement Decorator
def level_required(min_points):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.total_points >= min_points:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f"Insufficient level. You need {min_points} points to access this feature.")
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def min_level_required(min_level_value):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.level_value >= min_level_value:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Insufficient level. Claim your next level on your dashboard!")
                return redirect('dashboard')
        return _wrapped_view
    return decorator


def get_device_if_owner(request, device_id):
    device = get_object_or_404(SmartDevice, id=device_id)
    if device.room.apartment.occupant != request.user:
        return None
    return device


@login_required
def level_up(request):
    if request.method == 'POST':
        user = request.user
        points = user.total_points

        if user.level == 'Beginner' and points >= 3:
            user.level = 'Intermediate'
            messages.success(request, "Congratulations! You have unlocked the Intermediate level and device addition!")
        elif user.level == 'Intermediate' and points >= 5:
            user.level = 'Advanced'
            messages.success(request, "Congratulations! Advanced level reached. You can now configure and delete devices.")
        elif user.level == 'Advanced' and points >= 7:
            user.level = 'Expert'
            messages.success(request, "Congratulations! You are now an Expert. Statistics are unlocked.")
        else:
            messages.error(request, "You don't have enough points to claim this level yet.")

        user.save()
    return redirect('dashboard')