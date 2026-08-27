import os
import django
from faker import Faker
import random
import string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from smart_residence.models import Student, Apartment, Room, SmartDevice

fake = Faker('fr_FR')

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def populate(n=20):
    for i in range(n):
        first_name = fake.first_name()
        last_name = fake.last_name()

        username = f"{first_name[0].lower()}{last_name.lower()}_{random.randint(10, 99)}"
        email = f"{username}@student.cytech.fr"
        phone = fake.phone_number()
        student_id = str(random.randint(20000000, 29999999))
        age = random.randint(17, 26)
        sex = random.choice(['M', 'F'])

        raw_password = generate_random_password()

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
            }
        )

        if created:
            user.set_password(raw_password)
            user.save()
            print(f"Student created: {username}")

            apartment = Apartment.objects.create(
                address=fake.street_address(),
                apartment_number=str(random.randint(1, 500)),
                occupant=user
            )

            room_types = ['Kitchen', 'Living Room', 'Bedroom', 'Bathroom']
            nb_rooms = random.randint(2, 4)
            selected_rooms = random.sample(room_types, nb_rooms)

            for room_name in selected_rooms:
                room = Room.objects.create(
                    name=room_name,
                    apartment=apartment
                )

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
                        room=room
                    )
            print(f"  -> Apartment n°{apartment.apartment_number} generated with {nb_rooms} rooms.")
        else:
            print(f"Student {username} already exists.")

if __name__ == '__main__':
    print("Starting database population...")
    populate(20)
    print("Operation completed successfully!")