from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
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

    VENDOR_TYPES = [
        ('wholesaler', 'Wholesaler'),
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    # Vendor Profile Builder Auth
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Added fields based on visual reference and requirements
    vendor_type = models.CharField(max_length=50, choices=VENDOR_TYPES, default='wholesaler')
    country = models.CharField(max_length=100, default='United States')
    registration_number = models.CharField(max_length=100, blank=True)
    stock_symbol = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    internal_rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='represented_vendors')
    relationship_start_date = models.DateField(default=date.today)

    # Contact Info
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Financials (visual cue)
    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Verification Logic
        if self.status == 'verified':
            if not self.pk:
                raise ValidationError("Cannot verify a new vendor. Create the vendor first, add certifications, then verify.")

            # Check for at least one valid certification
            valid_certs = self.certs.filter(expiry_date__gte=date.today(), is_current=True)
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
