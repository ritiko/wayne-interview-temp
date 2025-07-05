from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from files.models import FileUpload
from files.serializers import FileListSerializer, FileUploadSerializer, FileStatusSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from files.tasks import process_csv_file
from django.core.cache import cache


class FileUploadView(generics.CreateAPIView):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        upload = serializer.save(user=self.request.user)
        process_csv_file.delay(str(upload.fileId))
        
    
class FileUploadStatusView(generics.RetrieveAPIView):
    queryset = FileUpload.objects.all()
    serializer_class = FileStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'fileId'

    def get_object(self):
        try:
            return FileUpload.objects.get(fileId=self.kwargs['fileId'], user=self.request.user)
        except FileUpload.DoesNotExist:
            raise NotFound(detail="File not found.")
    

class FileUploadListView(generics.ListAPIView):
    serializer_class = FileListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cache_key = f"user_file_ids:{user.id}"
        
        # Try cached file IDs
        cached_file_ids = cache.get(cache_key)
        if cached_file_ids is not None:
            return FileUpload.objects.filter(fileId__in=cached_file_ids, user=user).only('fileId', 'created_at')

        # If not cached, fetch from DB
        queryset = FileUpload.objects.filter(user=user).order_by('-created_at').only('fileId', 'created_at')
        file_ids = list(queryset.values_list('fileId', flat=True))
        cache.set(cache_key, file_ids, timeout=120)
        return queryset
