from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import uuid
import hashlib
import os

def hashed_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename_base, ext = os.path.splitext(filename)
    new_filename = uuid.uuid4().hex
    return f'certs/{new_filename}{ext}'

class Vendor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('inactive', 'Inactive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    # Adding user field for Vendor Profile Builder authentication
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.status == 'verified':
            if not self.pk:
                raise ValidationError("Cannot verify a new vendor. Create the vendor first, add certifications, then verify.")

            valid_certs = self.certs.filter(expiry_date__gte=timezone.now().date(), is_current=True)
            if not valid_certs.exists():
                raise ValidationError("Cannot verify vendor without at least one valid certification.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Certification(models.Model):
    CERT_TYPES = [
        ('ISO', 'ISO'),
        ('FDA', 'FDA'),
        ('CE', 'CE'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='certs')
    cert_type = models.CharField(max_length=50, choices=CERT_TYPES)
    file = models.FileField(upload_to=hashed_upload_path)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    is_current = models.BooleanField(default=True)

    def clean(self):
        if self.issue_date and self.expiry_date and self.expiry_date <= self.issue_date:
            raise ValidationError("Expiry date must be in the future relative to issue date.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        from datetime import date
        return self.expiry_date >= date.today() and self.is_current

    def __str__(self):
        return f"{self.vendor.name} - {self.cert_type}"

class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='active', vendor__status='verified')

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    objects = models.Manager()
    active_objects = ActiveProductManager()

    @property
    def is_active(self):
        return self.status == 'active' and self.vendor.status == 'verified'

    def __str__(self):
        return self.name

class VendorHistory(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.name} changed to {self.status} at {self.timestamp}"
