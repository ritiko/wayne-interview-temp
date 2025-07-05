from django.urls import path
from files.views import FileUploadView, FileUploadStatusView, FileUploadListView


urlpatterns = [
    path('upload/', FileUploadView.as_view(), name="file-upload"),
    path('status/<uuid:fileId>/', FileUploadStatusView.as_view(), name="file-status-view"),
    path('my-files/', FileUploadListView.as_view(), name="user-file-list"),
]