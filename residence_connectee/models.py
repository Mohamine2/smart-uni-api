from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal

class Student(AbstractUser):
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    student_id = models.CharField(max_length=20, unique=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Beginner')

    login_points = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    browsing_points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    @property
    def total_points(self):
        return self.login_points + self.browsing_points

    @property
    def level_value(self):
        values = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2, 'Expert': 3}
        return values.get(self.level, 0)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Level: {self.level} ({self.total_points} pts)"

class Apartment(models.Model):
    address = models.CharField(max_length=255)
    apartment_number = models.CharField(max_length=10)
    occupant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apartments'
    )

    def __str__(self):
        return f"Apartment {self.apartment_number} ({self.occupant.username})"

class Room(models.Model):
    NAME_CHOICES = [
        ('Kitchen', 'Kitchen'),
        ('Living Room', 'Living Room'),
        ('Bedroom', 'Bedroom'),
        ('Bathroom', 'Bathroom')
    ]
    name = models.CharField(max_length=50, choices=NAME_CHOICES)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='rooms')

    def __str__(self):
        return f"{self.name} - Apartment {self.apartment.apartment_number}"

class SmartDevice(models.Model):
    TYPE_CHOICES = [('Lamp', 'Lamp'), ('Thermostat', 'Thermostat'), ('Plug', 'Plug')]
    CONNECTIVITY_CHOICES = [('Wi-Fi', 'Wi-Fi'), ('Bluetooth', 'Bluetooth'), ('Zigbee', 'Zigbee')]

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True, null=True)
    is_on = models.BooleanField(default=False)
    power_consumption = models.FloatField(default=0.0)
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=50, blank=True, null=True)
    connectivity = models.CharField(max_length=20, choices=CONNECTIVITY_CHOICES, blank=True, null=True)
    battery_level = models.PositiveIntegerField(blank=True, null=True)
    last_interaction = models.DateTimeField(blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='devices')

    def __str__(self):
        return f"{self.name} ({self.room.name})"

class News(models.Model):
    CATEGORY_CHOICES = [
        ('RESIDENCE', 'Residence Life'),
        ('LOCAL', 'Local News'),
        ('URGENT', 'Alert / Maintenance'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    publication_date = models.DateTimeField(default=timezone.now)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='RESIDENCE')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ['-publication_date']

class StudyRoom(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"

class StudyRoomReservation(models.Model):
    study_room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='reservations')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Reservation by {self.student.username} - {self.study_room.name} on {self.reservation_date}"