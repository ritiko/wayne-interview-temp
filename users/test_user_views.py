from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User


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
