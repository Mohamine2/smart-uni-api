from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.db.models import Sum, Q
from decimal import Decimal
from rest_framework import viewsets

from .models import Student, News, SmartDevice, Room, StudyRoom, StudyRoomReservation, Apartment
from .forms import StudentRegistrationForm, SmartDeviceForm, RenameDeviceForm, ManageDeviceForm, ProfileEditForm, \
    RoomReservationForm
from .serializers import SmartDeviceSerializer, StudyRoomReservationSerializer


class SmartDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = SmartDeviceSerializer
    queryset = SmartDevice.objects.select_related('room')

    def get_queryset(self):
        return self.queryset.filter(room__apartment__occupant=self.request.user)

class StudyRoomReservationViewSet(viewsets.ModelViewSet):
    serializer_class = StudyRoomReservationSerializer
    queryset = StudyRoomReservation.objects.select_related('study_room', 'student').all()

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)



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

def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    return render(request, 'news_detail.html', {'news_item': news_item})


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

@login_required
def my_reservations(request):
    reservations = StudyRoomReservation.objects.filter(student=request.user).order_by('-reservation_date', '-start_time')
    return render(request, 'my_reservations.html', {'reservations': reservations})

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(StudyRoomReservation, id=reservation_id, student=request.user)

    if request.method == 'POST':
        reservation.delete()
        messages.success(request, "Reservation successfully canceled.")
        return redirect('my_reservations')

    return redirect('my_reservations')


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


@login_required
def book_study_room(request):
    if request.method == 'POST':
        form = RoomReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.student = request.user

            # Time check
            conflict = StudyRoomReservation.objects.filter(
                study_room=reservation.study_room,
                reservation_date=reservation.reservation_date
            ).filter(
                Q(start_time__lt=reservation.end_time, end_time__gt=reservation.start_time)
            ).exists()

            if conflict:
                messages.error(request, f"Sorry, the {reservation.study_room.name} is already booked during this time slot.") # Modifié ici
            else:
                reservation.save()

                request.user.browsing_points += Decimal('0.50')
                request.user.save()

                messages.success(request, "Reservation confirmed!")
                return redirect('dashboard')
        else:
            messages.error(request, "Error in the dates or time entered")
    else:
        form = RoomReservationForm()

    rooms = StudyRoom.objects.all()
    return render(request, 'book_room.html', {'form': form, 'rooms': rooms})


# --- 3. CONNECTED DEVICES MODULE ---

def search_devices(request):
    keyword = request.GET.get('q', '')
    selected_type = request.GET.get('device_type', '')
    selected_status = request.GET.get('status', '')
    selected_room = request.GET.get('room', '')

    devices = SmartDevice.objects.all()

    if keyword:
        devices = devices.filter(name__icontains=keyword)
    if selected_type:
        devices = devices.filter(device_type=selected_type)
    if selected_status == 'active':
        devices = devices.filter(is_on=True)
    elif selected_status == 'inactive':
        devices = devices.filter(is_on=False)
    if selected_room:
        devices = devices.filter(room_id=selected_room)

    rooms = Room.objects.all()

    context = {
        'devices': devices,
        'rooms': rooms,
        'keyword': keyword,
        'selected_type': selected_type,
        'selected_status': selected_status,
        'selected_room': selected_room,
        'type_choices': SmartDevice.TYPE_CHOICES,
    }

    return render(request, 'search_devices.html', context)

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


@login_required
@min_level_required(1)
def add_device(request):
    my_accommodations = Apartment.objects.filter(occupant=request.user)
    my_rooms = Room.objects.filter(apartment__in=my_accommodations)

    if request.method == 'POST':
        form = SmartDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)

            if device.room in my_rooms:
                device.is_on = False
                device.consumption = 0.0
                device.save()

                request.user.browsing_points += Decimal('0.50')
                request.user.save()

                messages.success(request, "Device successfully added !")
                return redirect('dashboard')
            else:
                messages.error(request, "Attempt to add an item to an unauthorized room.")
        else:
            messages.error(request, "Error in form")
    else:
        form = SmartDeviceForm()
        form.fields['room'].queryset = my_rooms

    context = {
        'form': form,
        'rooms': my_rooms,
        'type_choices': SmartDevice.TYPE_CHOICES
    }
    return render(request, 'add_device.html', context)


@login_required
@level_required(1)
def rename_device(request, device_id):
    device = get_device_if_owner(request, device_id)
    if not device:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = RenameDeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, "The object has been successfully renamed.")
            return redirect('dashboard')
    else:
        form = RenameDeviceForm(instance=device)

    return render(request, 'rename_device.html', {'form': form, 'device': device})


@login_required
@min_level_required(2)
def delete_device(request, device_id):
    device = get_device_if_owner(request, device_id)
    if not device:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    device.delete()
    request.user.browsing_points += Decimal('0.50')
    request.user.save()
    messages.success(request, "The device has been deleted.")
    return redirect('dashboard')


@login_required
@level_required(2)
def configure_device(request, device_id):
    device = get_device_if_owner(request, device_id)
    if not device:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ManageDeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save(commit=False)

            if not device.is_on:
                device.power_consumption = 0.0

            device.save()

            request.user.browsing_points += Decimal('0.50')
            request.user.save()

            messages.success(request, f"Settings for {device.name} were updated.")
            return redirect('dashboard')
        else:
            messages.error(request, "Error in the settings. Please check your entries.")
    else:
        form = ManageDeviceForm(instance=device)

    return render(request, 'configure_device.html', {'form': form, 'device': device})

@login_required
@min_level_required(3)
def consumption_statistics(request):
    my_apartments = request.user.apartments.all()
    my_devices = SmartDevice.objects.filter(room__apartment__in=my_apartments)

    aggregation = my_devices.aggregate(total=Sum('power_consumption'))

    if aggregation['total'] is None:
        total_consumption = 0.0
    else:
        total_consumption = float(aggregation['total'])

    active_devices = my_devices.filter(is_on=True)
    inactive_devices = my_devices.filter(is_on=False)

    context = {
        'total_consumption': total_consumption,
        'active_count': active_devices.count(),
        'inactive_count': inactive_devices.count(),
        'active_devices': active_devices,
    }
    return render(request, 'statistics.html', context)