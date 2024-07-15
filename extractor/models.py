from django.db import models

class UploadedExcel(models.Model):
    excel_file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
# models.py

