from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from unittest.mock import patch
from users.models import User
from files.models import FileUpload
from files.tasks import process_csv_file, retry_stuck_files
import tempfile
import os 


class FileUploadViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="fileuser",
            email="fileuser@qq.com",
            password="StrongPass!123"
        )
        self.upload_url = reverse('file-upload')  
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        for upload in FileUpload.objects.all():
            if upload.file and os.path.exists(upload.file.path):
                os.remove(upload.file.path)

    @patch('files.views.process_csv_file.delay')
    def test_upload_valid_csv_file(self, mock_process_task):
        csv_file = SimpleUploadedFile("test.csv", b"col1,col2\nval1,val2\n", content_type="text/csv")

        response = self.client.post(self.upload_url, {"file": csv_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FileUpload.objects.count(), 1)
        self.assertEqual(FileUpload.objects.first().user, self.user)
        mock_process_task.assert_called_once()  # Celery task triggered

    def test_upload_non_csv_file(self):
        txt_file = SimpleUploadedFile("test.txt", b"invalid", content_type="text/plain")

        response = self.client.post(self.upload_url, {"file": txt_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)
        self.assertEqual(FileUpload.objects.count(), 0)

    def test_upload_too_large_file(self):
        large_file = tempfile.NamedTemporaryFile(suffix=".csv")
        large_file.write(b"A" * (10 * 1024 * 1024 + 1))  # >10MB
        large_file.seek(0)

        with open(large_file.name, 'rb') as f:
            file_data = SimpleUploadedFile("large.csv", f.read(), content_type="text/csv")
            response = self.client.post(self.upload_url, {"file": file_data}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)
        self.assertEqual(FileUpload.objects.count(), 0)

    def test_upload_requires_authentication(self):
        self.client.force_authenticate(user=None)
        csv_file = SimpleUploadedFile("test.csv", b"col1,col2", content_type="text/csv")

        response = self.client.post(self.upload_url, {"file": csv_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("files.tasks.send_mail")
    @patch("files.tasks.time.sleep", return_value=None)
    def test_email_sent_after_task_completion(self, mock_sleep, mock_send_mail):
        # Upload file through model (simulate view logic already tested)
        test_file = SimpleUploadedFile("email_test.csv", b"col1,col2\nval1,val2", content_type="text/csv")
        upload = FileUpload.objects.create(user=self.user, file=test_file)

        # Call task directly
        process_csv_file(str(upload.fileId))

        # Refresh file upload instance
        upload.refresh_from_db()
        self.assertEqual(upload.status, 'completed')

        # Email should have been triggered
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args

        self.assertEqual(kwargs['subject'], "Your file has been processed")
        self.assertIn(self.user.email, kwargs['recipient_list'])
        self.assertIn("Your uploaded CSV file", kwargs['message'])

    @patch("files.tasks.process_csv_file.delay")
    def test_retry_stuck_files_triggers_for_old_processing_files(self, mock_process_delay):
        # Create a stuck file in "processing" state older than 30 minutes
        stuck_time = timezone.now() - timedelta(minutes=31)
        stuck_file = FileUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("stuck.csv", b"col1,col2", content_type="text/csv"),
            status="processing",
        )
        
        FileUpload.objects.filter(pk=stuck_file.pk).update(updated_at=stuck_time)

        # Call the periodic retry task directly
        retry_stuck_files()

        # Assert: Check if task was retried
        mock_process_delay.assert_called_once_with(str(stuck_file.fileId))

    @patch("files.tasks.process_csv_file.delay")
    def test_retry_stuck_files_ignores_recent_processing_files(self, mock_process_delay):
        # Create a file still "processing" but updated recently
        recent_time = timezone.now() - timedelta(minutes=5)
        FileUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("recent.csv", b"col1,col2", content_type="text/csv"),
            status="processing",
            updated_at=recent_time
        )
        
        # Call the retry task
        retry_stuck_files()

        # Should NOT retry
        mock_process_delay.assert_not_called()

     
    def test_get_file_status_success(self):
        csv_file = SimpleUploadedFile("status_test.csv", b"col1,col2\nval1,val2", content_type="text/csv")
        upload = FileUpload.objects.create(user=self.user, file=csv_file)

        url = reverse('file-status-view', kwargs={'fileId': str(upload.fileId)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fileId'], str(upload.fileId))
        self.assertEqual(response.data['status'], upload.status)


    def test_get_file_status_unauthorized_access(self):
        other_user = User.objects.create_user(
            username="otheruser", email="other@qq.com", password="Password123"
        )
        other_file = FileUpload.objects.create(
            user=other_user,
            file=SimpleUploadedFile("other.csv", b"col1,col2", content_type="text/csv")
        )

        url = reverse('file-status-view', kwargs={'fileId': str(other_file.fileId)})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("File not found", str(response.data))


    def test_get_file_status_not_found(self):
        fake_file_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        url = reverse('file-status-view', kwargs={'fileId': fake_file_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("File not found", str(response.data))
        

class FileUploadListViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="listuser",
            email="listuser@example.com",
            password="StrongPass123!"
        )
        self.url = reverse("user-file-list")
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        cache.clear()
        for upload in FileUpload.objects.all():
            if upload.file and os.path.exists(upload.file.path):
                os.remove(upload.file.path)

    def test_list_files_without_cache(self):
        file1 = FileUpload.objects.create(user=self.user)
        file2 = FileUpload.objects.create(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        returned_ids = [file["fileId"] for file in response.data]
        self.assertIn(str(file1.fileId), returned_ids)
        self.assertIn(str(file2.fileId), returned_ids)

    def test_list_files_with_cache(self):
        file1 = FileUpload.objects.create(user=self.user)
        file2 = FileUpload.objects.create(user=self.user)

        # Set cache manually
        cache_key = f"user_file_ids:{self.user.id}"
        cache.set(cache_key, [str(file1.fileId)], timeout=120)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["fileId"], str(file1.fileId))

    def test_list_files_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

