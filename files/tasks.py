import time
import random
import logging
from celery import shared_task
from .models import FileUpload
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone



logger = logging.getLogger(__name__)

@shared_task(name='process_csv_file')
def process_csv_file(file_id):
    try:
        logger.info(f"[START] Received task to process file ID: {file_id}")
        upload = FileUpload.objects.get(fileId=file_id)

        logger.info(f"[PROCESSING] Updating file {file_id} status to 'processing'")
        upload.status = 'processing'
        upload.save()

        delay = random.randint(30, 60)
        logger.info(f"[WAITING] Simulating processing for {delay} seconds for file {file_id}")
        time.sleep(delay)

        logger.info(f"[COMPLETED] Updating file {file_id} status to 'completed'")
        upload.status = 'completed'
        upload.save()
        
        logger.info(f"[EMAIL] Sending email to {upload.user.email} for file {file_id}")
        send_mail(
            subject="Your file has been processed",
            message=f"Hello {upload.user.username},\n\nYour uploaded CSV file '{upload.fileId}' has been successfully processed.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[upload.user.email],
            fail_silently=False,
        )
    except FileUpload.DoesNotExist:
        logger.error(f"[ERROR] FileUpload with ID {file_id} does not exist")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error while processing file {file_id}: {str(e)}")
        

@shared_task(name='retry_stuck_files')
def retry_stuck_files():
    stuck_threshold = timezone.now() - timedelta(minutes=30)
    stuck_files = FileUpload.objects.filter(status='processing', updated_at__lt=stuck_threshold)

    if not stuck_files.exists():
        logger.info("[RETRY-TASK] No stuck files found.")
        return

    logger.warning(f"[RETRY-TASK] Retrying {stuck_files.count()} stuck file(s)...")

    for file in stuck_files:
        logger.warning(f"[RETRY-TASK] Retrying file ID: {file.fileId}")
        process_csv_file.delay(str(file.fileId))
