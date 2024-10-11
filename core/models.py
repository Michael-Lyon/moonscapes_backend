# myapp/models.py
from django.db import models


class UploadedImage(models.Model):
    image = models.ImageField(upload_to='images/')
    task_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='processing')
    model_data = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    glb_file = models.FileField(upload_to='models/', null=True, blank=True)
    usdz_file = models.FileField(upload_to='models/', null=True, blank=True)

    def __str__(self):
        return self.task_id



class FileUpload(models.Model):
    usdz_file = models.FileField(upload_to='uploads/usdz/', null=True, blank=True)
    glb_file = models.FileField(upload_to='uploads/glb/', null=True, blank=True)
    json_file = models.FileField(upload_to='uploads/json/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='uploads/thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File {self.id} uploaded at {self.created_at}"