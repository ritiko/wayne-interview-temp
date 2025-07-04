from rest_framework import serializers
from .models import FileUpload


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['file', 'fileId', 'status']
        read_only_fields = ['fileId', 'status']

    def validate_file(self, value):
        if not value.name.lower().endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 10MB.")
        return value


class FileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['fileId', 'status', 'created_at', 'file']
        read_only_fields = fields
