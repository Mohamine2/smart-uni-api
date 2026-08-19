from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal
from datetime import date, time

from .models import (
    Apartment,
    News,
    Room,
    SmartDevice,
    Student,
    StudyRoom,
    StudyRoomReservation,
)


# ==============================================================================
# BASE TEST CLASS FOR USER-SCOPED RESOURCES
# ==============================================================================

class BaseUserOwnedResourceTest():
    """
    Base test class to verify data isolation and ownership enforcement.
    Flagged with __test__ = False so unittest does not run it directly.
    """

    def setUp(self):
        # Create two regular students
        self.user1 = Student.objects.create_user(
            username="user1",
            password="password123",
        )
        self.user2 = Student.objects.create_user(
            username="user2",
            password="password123",
        )

        # Populate model-specific test fixtures
        self.setup_resource_data()

    def setup_resource_data(self):
        raise NotImplementedError("Child classes must implement setup_resource_data.")

    # --- Common Security & Isolation Tests ---

    def test_unauthenticated_user_cannot_access_endpoints(self):
        """Verify anonymous requests are rejected with 401 Unauthorized."""
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(
            self.client.get(self.detail_url_user1).status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_authenticated_user_sees_only_own_items(self):
        """Verify the list endpoint scopes results strictly to the authenticated user."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure only user1's resource is returned despite multiple objects existing
        self.assertEqual(len(response.data), 1)

    def test_cannot_access_other_users_item(self):
        """Verify accessing another user's item returns 404 Not Found (hidden by get_queryset)."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get(self.detail_url_user2)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_delete_other_users_item(self):
        """Verify attempting to delete another user's item returns 404 Not Found."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.delete(self.detail_url_user2)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ==============================================================================
# SMART DEVICE TESTS
# ==============================================================================

class SmartDeviceViewSetTests(BaseUserOwnedResourceTest):

    def setup_resource_data(self):
        """Set up Apartment -> Room -> Device hierarchy for both users."""
        # Resources for user1
        self.apartment_user1 = Apartment.objects.create(occupant=self.user1)
        self.room_user1 = Room.objects.create(apartment=self.apartment_user1)
        self.device_user1 = SmartDevice.objects.create(
            name="Living Room Light",
            room=self.room_user1,
        )

        # Resources for user2
        self.apartment_user2 = Apartment.objects.create(occupant=self.user2)
        self.room_user2 = Room.objects.create(apartment=self.apartment_user2)
        self.device_user2 = SmartDevice.objects.create(
            name="Bedroom Thermostat",
            room=self.room_user2,
        )

        # URLs required by BaseUserOwnedResourceTest
        self.list_url = reverse('smartdevice-list')
        self.detail_url_user1 = reverse(
            'smartdevice-detail',
            kwargs={'pk': self.device_user1.pk}
        )
        self.detail_url_user2 = reverse(
            'smartdevice-detail',
            kwargs={'pk': self.device_user2.pk}
        )

    def test_owner_can_modify_own_device(self):
        """Verify nominal PATCH update by resource owner."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.patch(
            self.detail_url_user1,
            {'name': 'Updated Light Name'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device_user1.refresh_from_db()
        self.assertEqual(self.device_user1.name, 'Updated Light Name')

    def test_user_cannot_create_device_in_another_users_room(self):
        """Prevent attaching a new device to another user's room (IDOR prevention)."""
        self.client.force_authenticate(user=self.user1)

        payload = {
            'name': 'Rogue Device',
            'room': self.room_user2.pk,
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(SmartDevice.objects.filter(name='Rogue Device').exists())


# ==============================================================================
# STUDY ROOM RESERVATION TESTS
# ==============================================================================

class StudyRoomReservationViewSetTests(BaseUserOwnedResourceTest):
    def setup_resource_data(self):
        """Set up shared StudyRoom and user reservations."""
        self.study_room = StudyRoom.objects.create(
            name="Study Room A",
            capacity=10,
        )

        # Reservation belonging to user1
        self.reservation_user1 = StudyRoomReservation.objects.create(
            student=self.user1,
            study_room=self.study_room,
        )

        # Reservation belonging to user2
        self.reservation_user2 = StudyRoomReservation.objects.create(
            student=self.user2,
            study_room=self.study_room,
        )

        # URLs required by BaseUserOwnedResourceTest
        self.list_url = reverse('studyroomreservation-list')
        self.detail_url_user1 = reverse(
            'studyroomreservation-detail',
            kwargs={'pk': self.reservation_user1.pk}
        )
        self.detail_url_user2 = reverse(
            'studyroomreservation-detail',
            kwargs={'pk': self.reservation_user2.pk}
        )

    def test_perform_create_assigns_logged_in_user(self):
        """Verify perform_create enforces the authenticated user as the reservation owner."""
        self.client.force_authenticate(user=self.user1)

        payload = {
            'study_room': self.study_room.pk,
            # Attempting to assign the reservation to user2
            'student': self.user2.pk,
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_reservation = StudyRoomReservation.objects.get(id=response.data['id'])
        # Verify the backend overrode the payload value with request.user
        self.assertEqual(created_reservation.student, self.user1)

    def test_cannot_book_overlapping_slot(self):
        """Prevents the creation of a reservation that overlaps with an existing time slot."""
        StudyRoomReservation.objects.create(
            student=self.user2,
            study_room=self.study_room,
            reservation_date=date(2026, 9, 1),
            start_time=time(14,0),
            end_time=time(16, 0),
        )

        self.client.force_authenticate(user=self.user1)

        # Overlapping booking attempt: 3 PM – 5 PM
        payload = {
            'study_room': self.study_room.pk,
            'reservation_date': '2026-09-01',
            'start_time': '15:00:00',
            'end_time': '17:00:00',
        }

        response = self.user1.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# NEWS TESTS (IsAdminOrReadOnly PERMISSION)
# ==============================================================================

class NewsViewSetTests(APITestCase):
    def setUp(self):
        # Regular student (non-staff)
        self.regular_user = Student.objects.create_user(
            username="student_user",
            password="password123",
            is_staff=False,
        )

        # Admin / Staff user
        self.admin_user = Student.objects.create_user(
            username="admin_user",
            password="password123",
            is_staff=True,
        )

        # Existing news fixture
        self.news = News.objects.create(
            title="Building Maintenance",
            content="Elevator maintenance scheduled for tomorrow morning.",
        )

        self.list_url = reverse('news-list')
        self.detail_url = reverse('news-detail', kwargs={'pk': self.news.pk})

    # --- Read Operations (Public / Safe Methods) ---

    def test_unauthenticated_user_can_list_news(self):
        """Verify anonymous users can access the news list (GET)."""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_user_can_retrieve_news_detail(self):
        """Verify anonymous users can read a specific news article (GET)."""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.news.pk)

    # --- Write Operations: Non-Staff Access Rejection ---

    def test_unauthenticated_user_cannot_create_news(self):
        """Verify anonymous users cannot publish news (POST)."""
        payload = {'title': 'Spam Title', 'content': 'Spam Content'}
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create_news(self):
        """Verify authenticated non-staff users cannot publish news (POST)."""
        self.client.force_authenticate(user=self.regular_user)

        payload = {'title': 'Student Post', 'content': 'Party tonight!'}
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(News.objects.filter(title='Student Post').exists())

    def test_regular_user_cannot_modify_news(self):
        """Verify authenticated non-staff users cannot modify news (PATCH)."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.patch(
            self.detail_url,
            {'title': 'Tampered Title'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.news.refresh_from_db()
        self.assertNotEqual(self.news.title, 'Tampered Title')

    def test_regular_user_cannot_delete_news(self):
        """Verify authenticated non-staff users cannot delete news (DELETE)."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(News.objects.filter(pk=self.news.pk).exists())

    # --- Write Operations: Staff Access Authorization ---

    def test_staff_user_can_create_news(self):
        """Verify staff members can successfully create a news article (POST)."""
        self.client.force_authenticate(user=self.admin_user)

        payload = {
            'title': 'New Cafeteria Menu',
            'content': 'Check out our new weekly schedule.',
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(News.objects.filter(title='New Cafeteria Menu').exists())

    def test_staff_user_can_modify_news(self):
        """Verify staff members can modify an existing news article (PATCH)."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {'title': 'Updated Maintenance Notice'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.news.refresh_from_db()
        self.assertEqual(self.news.title, 'Updated Maintenance Notice')

    def test_staff_user_can_delete_news(self):
        """Verify staff members can delete an existing news article (DELETE)."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(News.objects.filter(pk=self.news.pk).exists())

    def test_authenticated_user_earns_browsing_points_on_retrieve(self):
        """Verify that a logged-in student earns 0.50 points when viewing an article."""
        self.client.force_authenticate(user=self.regular_user)
        initial_points = self.regular_user.browsing_points

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.regular_user.refresh_from_db()
        self.assertEqual(
            self.regular_user.browsing_points,
            initial_points + Decimal('0.50')
        )

    def test_unauthenticated_user_retrieve_does_not_crash(self):
        """Verify that an anonymous user can read an article without browsing_points errors."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_news_by_search_keyword(self):
        """Verify text search by title or content."""
        News.objects.create(
            title="Power Outage",
            content="2 hours maintenance"
        )

        # Search for the "Power" keyword
        response = self.client.get(f"{self.list_url}?search=Power")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Power Outage")