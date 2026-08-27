import os
import django
from datetime import datetime
from django.utils.timezone import make_aware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from smart_residence.models import News

def populate_news():
    print("Cleaning database...")
    News.objects.all().delete()

    news_data = [
        {
            "title": "Smart Thermostat Deployment",
            "content": "Installation scheduled in Building A. These devices will reduce energy consumption by 20%.",
            "category": "RESIDENCE",
            "publication_date": make_aware(datetime(2026, 4, 15, 10, 30))
        },
        {
            "title": "Wi-Fi Maintenance",
            "content": "Nightly shutdown for fiber installation next Wednesday from 2 AM to 5 AM.",
            "category": "URGENT",
            "publication_date": make_aware(datetime(2026, 4, 17, 14, 0))
        }
    ]

    for data in news_data:
        News.objects.create(**data)
        print(f" -> Created: {data['title']}")

if __name__ == '__main__':
    populate_news()