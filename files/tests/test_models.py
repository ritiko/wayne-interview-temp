from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from users.models import User
from files.models import FileUpload 
from files.choices import PENDING
import uuid

class FileUploadModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='securepass123'
        )

        self.test_file = SimpleUploadedFile(
            "test_file.csv",
            b"col1,col2\nval1,val2\n",
            content_type="text/csv"
        )

        self.file_upload = FileUpload.objects.create(
            file=self.test_file,
            user=self.user
        )

    def test_file_upload_creation(self):
        self.assertEqual(self.file_upload.user, self.user)
        self.assertTrue(self.file_upload.file.name.startswith("uploads/test_file"))
        self.assertEqual(self.file_upload.status, PENDING)
        self.assertIsInstance(self.file_upload.fileId, uuid.UUID)

    def test_str_returns_filename(self):
        self.assertEqual(str(self.file_upload), self.file_upload.file.name)

    def test_created_at_auto_set(self):
        self.assertLessEqual(self.file_upload.created_at, timezone.now())
