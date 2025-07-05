from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()

class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='wayne@gmail.com',
            username='wayneuser',
            password='securepassword123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'wayne@gmail.com')
        self.assertEqual(self.user.username, 'wayneuser')
        self.assertTrue(self.user.check_password('securepassword123'))

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='wayne@gmail.com',
                username='anotheruser',
                password='anotherpassword'
            )

    def test_str_method(self):
        self.assertEqual(str(self.user), 'wayne@gmail.com')
