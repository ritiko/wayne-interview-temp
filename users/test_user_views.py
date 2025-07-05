from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


class UserRegistrationTests(APITestCase):
    
    def test_user_registration_success(self):
        payload = {
            "username": "wayne",
            "email": "wayne@gmail.com",
            "password": "StrongPass!123",
            "confirm_password": "StrongPass!123"
        }
        response = self.client.post(reverse('user-registration'), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="wayne@gmail.com").exists())

    def test_user_registration_password_mismatch(self):
        payload = {
            "username": "wayne2",
            "email": "wayne2@gmail.com",
            "password": "StrongPass!123",
            "confirm_password": "WrongPass!123"
        }
        response = self.client.post(reverse('user-registration'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    def test_user_registration_missing_special_character(self):
        payload = {
            "username": "wayne3",
            "email": "wayne3@gmail.com",
            "password": "Password123",  # No special character as per the custom validator
            "confirm_password": "Password123"
        }
        response = self.client.post(reverse('user-registration'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_registration_duplicate_email(self):
        User.objects.create_user(
            username="original", 
            email="wayne@gmail.com", 
            password="Somepass!123"
        )

        payload = {
            "username": "wayne4",
            "email": "wayne@gmail.com", # duplicate email
            "password": "AnotherPass!123",
            "confirm_password": "AnotherPass!123"
        }
        response = self.client.post(reverse('user-registration'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


    def test_user_registration_duplicate_username(self):
        User.objects.create_user(
            username="wayne_og",
            email="wayne01@gmail.com",
            password="ExistingPass!123"
        )

        payload = {
            "username": "wayne_og",  # duplicate username
            "email": "wayneuser@gmail.com",
            "password": "NewPass!123",
            "confirm_password": "NewPass!123"
        }

        response = self.client.post(reverse('user-registration'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        

class UserLoginTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="userwayne",
            email="user@outlook.com",
            password="TestPassword!123"
        )
        self.login_url = reverse('token_obtain_pair')

    def test_user_login_success(self):
        payload = {
            "email": "user@outlook.com",
            "password": "TestPassword!123"
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_login_wrong_password(self):
        payload = {
            "email": "user@outlook.com",
            "password": "WrongPassword123"
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account found", str(response.data))

    def test_user_login_non_existent_email(self):
        payload = {
            "email": "nouser@outlook.com",
            "password": "TestPassword!123"
        }
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("No active account found", str(response.data))


class TokenRefreshTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="refreshuser",
            email="refreshuser@qq.com",
            password="RefreshPass!123"
        )
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_token_refresh_success(self):
        # Login to get refresh token
        login_response = self.client.post(self.login_url, {
            "email": "refreshuser@qq.com",
            "password": "RefreshPass!123"
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", login_response.data)

        refresh_token = login_response.data["refresh"]

        # Use refresh token to get new access token
        refresh_response = self.client.post(self.refresh_url, {
            "refresh": refresh_token
        })

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_token_refresh_invalid_token(self):
        response = self.client.post(self.refresh_url, {
            "refresh": "invalid.refresh.token"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class RefreshTokenBlacklistTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="blacklistuser",
            email="blacklist@qq.com",
            password="TestPass!123"
        )
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_refresh_token_is_blacklisted_after_rotation(self):
        # Login and get tokens
        response = self.client.post(self.login_url, {
            "email": "blacklist@qq.com",
            "password": "TestPass!123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_refresh = response.data['refresh']

        # Use refresh token to get new tokens
        refresh_response = self.client.post(self.refresh_url, {
            "refresh": old_refresh
        })
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh", refresh_response.data)

        # Confirm the old refresh token is blacklisted
        outstanding = OutstandingToken.objects.filter(user=self.user)
        blacklisted = BlacklistedToken.objects.filter(token__in=outstanding)

        # One of the outstanding tokens should now be blacklisted
        self.assertTrue(blacklisted.exists(), "Old refresh token should be blacklisted after rotation")