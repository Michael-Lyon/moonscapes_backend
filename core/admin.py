from django.contrib import admin

from core.models import FileUpload, UploadedImage

# Register your models here.

admin.site.register(UploadedImage)
admin.site.register(FileUpload)