from django.urls import path
from core.views import ImageStatusView, ImageUploadView, UploadFileView


app_name = "core"
urlpatterns = [
     path('base/upload/', UploadFileView.as_view(), name='upload_file'),
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('status/<str:task_id>/', ImageStatusView.as_view(), name='image-status'),
]
