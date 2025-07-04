from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from files.models import FileUpload
from files.serializers import FileUploadSerializer, FileStatusSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from files.tasks import process_csv_file


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