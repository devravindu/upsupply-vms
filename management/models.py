from django.db import models
import uuid

class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('verified', 'Verified')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Certification(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='certs')
    cert_type = models.CharField(max_length=50) # ISO, FDA, etc.
    file = models.FileField(upload_to='certs/')
    expiry_date = models.DateField()

    @property
    def is_valid(self):
        from datetime import date
        return self.expiry_date >= date.today()