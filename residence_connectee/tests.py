from django.contrib.auth import get_user_model

from residence_connectee.models import (
    Apartment,
    News,
    Room,
    SmartDevice,
    StudyRoom,
    StudyRoomReservation,
)

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

Student = get_user_model()

class AuthenticationTests(APITestCase):

    def setUp(self):
        # Primary test user
        self.student = Student.objects.create_user(
            username='test_user',
            password='test_password',
        )

        self.url = reverse('smartdevice-list')

    def test_access_denied_without_authentication(self):
        """
        Verify that an unauthenticated user cannot access
        the endpoint.

        We send a GET request without providing authentication.
        The API should return HTTP 401 (Unauthorized).
        """

        # Simulate a GET request to the endpoint.
        # No token or authentication information is provided.
        response = self.client.get(self.url)

        # Check that the API denies access with HTTP 401.
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_access_allowed_with_authentication(self):
        """
        Verify that an authenticated user can access
        the endpoint.
        """

        # Tell DRF that the request is made by our test user.
        self.client.force_authenticate(user=self.student)

        # Send the same GET request, this time as an authenticated user.
        response = self.client.get(self.url)

        # The request should be accepted: HTTP 200 (OK).
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_access_allowed_with_real_jwt(self):
        # Get the JWT token using the real token endpoint.
        token_url = reverse("token_obtain_pair")

        response = self.client.post(
            token_url,
            {
                "username": "test_user",
                "password": "test_password",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Extract the access token
        access_token = response.data["access"]

        # Add the JWT to the authorization header
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        # Access the protected endpoint
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_access_denied_with_invalid_jwt(self):
        # Send an invalid JWT.
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get(self.url)

        # The API should reject the invalid token.
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
