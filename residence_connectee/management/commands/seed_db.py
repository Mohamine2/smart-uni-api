import random
import string
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware
from faker import Faker

from residence_connectee.models import (
    Apartment,
    News,
    Room,
    SmartDevice,
    Student,
    StudyRoom,
)

fake = Faker('fr_FR')


class Command(BaseCommand):
    help = "Populates the Smart-Uni database with initial data (News, Study Rooms, Students, Apartments, Devices)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            type=int,
            default=20,
            help="Number of students (and associated apartments) to generate (default: 20)",
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help="Delete existing news and records before seeding",
        )

    def _generate_random_password(self, length=12):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def _seed_study_rooms(self):
        self.stdout.write("1/3 Populating study rooms...")
        study_rooms_data = [
            {"name": "Turing Room", "capacity": 10, "description": "Quiet zone with shared screens."},
            {"name": "North Library", "capacity": 30, "description": "Absolute silence required."},
            {"name": "Coworking Space", "capacity": 15, "description": "Ideal for group projects."},
        ]

        for room_data in study_rooms_data:
            _, created = StudyRoom.objects.get_or_create(name=room_data['name'], defaults=room_data)
            status = "created" if created else "already exists"
            self.stdout.write(f"   -> Room {room_data['name']} ({status})")

    def _seed_news(self, clean=False):
        self.stdout.write("2/3 Populating news...")
        if clean:
            deleted_count, _ = News.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"   -> Deleted {deleted_count} existing news articles."))

        news_data = [
            {
                "title": "Smart Thermostat Deployment",
                "content": "Installation scheduled in Building A. These devices will reduce energy consumption by 20%.",
                "category": "RESIDENCE",
                "publication_date": make_aware(datetime(2026, 4, 15, 10, 30)),
            },
            {
                "title": "Wi-Fi Maintenance",
                "content": "Nightly shutdown for fiber installation next Wednesday from 2 AM to 5 AM.",
                "category": "URGENT",
                "publication_date": make_aware(datetime(2026, 4, 17, 14, 0)),
            },
        ]

        for data in news_data:
            News.objects.get_or_create(title=data['title'], defaults=data)
            self.stdout.write(f"   -> News created: {data['title']}")

    def _seed_students_and_apartments(self, n):
        self.stdout.write(f"3/3 Populating {n} students and apartments...")
        created_count = 0

        for _ in range(n):
            first_name = fake.first_name()
            last_name = fake.last_name()

            username = f"{first_name[0].lower()}{last_name.lower()}_{random.randint(10, 99)}"
            email = f"{username}@student.cytech.fr"
            phone = fake.phone_number()
            student_id = str(random.randint(20000000, 29999999))
            age = random.randint(17, 26)
            sex = random.choice(['M', 'F'])

            raw_password = self._generate_random_password()

            user, created = Student.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone_number': phone,
                    'student_id': student_id,
                    'age': age,
                    'sex': sex,
                    'is_active': True,
                },
            )

            if created:
                user.set_password(raw_password)
                user.save()
                created_count += 1

                apartment = Apartment.objects.create(
                    address=fake.street_address(),
                    apartment_number=str(random.randint(1, 500)),
                    occupant=user,
                )

                room_types = ['Kitchen', 'Living Room', 'Bedroom', 'Bathroom']
                nb_rooms = random.randint(2, 4)
                selected_rooms = random.sample(room_types, nb_rooms)

                for room_name in selected_rooms:
                    room = Room.objects.create(name=room_name, apartment=apartment)

                    device_types = ['Lamp', 'Thermostat', 'Plug']
                    nb_devices = random.randint(1, 3)

                    for _ in range(nb_devices):
                        device_type = random.choice(device_types)
                        device_name = f"{device_type} {random.randint(1, 5)}"

                        SmartDevice.objects.create(
                            name=device_name,
                            device_type=device_type,
                            is_on=random.choice([True, False]),
                            power_consumption=round(random.uniform(5.0, 150.0), 2),
                            room=room,
                        )

        self.stdout.write(f"   -> {created_count} new students generated with their apartments.")

    def handle(self, *args, **options):
        nb_students = options['students']
        clean = options['clean']

        self.stdout.write(self.style.MIGRATE_HEADING("=== Starting Smart-Uni database seeding ==="))

        try:
            with transaction.atomic():
                self._seed_study_rooms()
                self._seed_news(clean=clean)
                self._seed_students_and_apartments(nb_students)

            self.stdout.write(self.style.SUCCESS("\nDatabase populated successfully!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nSeeding failed: {e}"))