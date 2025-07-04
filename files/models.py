from django.db import models
from users.models import User
from .choices import UPLOAD_STATUS_CHOICES, PENDING

# Create your models here.
class FileUpload(models.Model):
    fileId = models.UUIDField(primary_key=True, editable=False)
    file = models.FileField(upload_to='uploads/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name