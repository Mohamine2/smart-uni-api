import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from smart_residence.models import StudyRoom

def populate_study_rooms():
    print("Starting study room population...")
    salles_data = [
        {"name": "Turing Room", "capacity": 10, "description": "Quiet zone with shared screens."},
        {"name": "North Library", "capacity": 30, "description": "Absolute silence required."},
        {"name": "Coworking Space", "capacity": 15, "description": "Ideal for group projects."},
    ]

    for s in salles_data:
        StudyRoom.objects.get_or_create(name=s['name'], defaults=s)

    print("Population completed successfully!")

if __name__ == '__main__':
    populate_study_rooms()