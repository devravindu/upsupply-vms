from datetime import date
import os
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import BooleanField, Case, Q, Value, When
from django.utils import timezone


def hashed_upload_path(instance, filename):
    _name, ext = os.path.splitext(filename)
    new_filename = uuid.uuid4().hex
    return f'certs/{new_filename}{ext}'


class VendorQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser or user.is_staff:
            return self
        return self.filter(Q(user=user) | Q(internal_rep=user))


class Vendor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('inactive', 'Inactive'),
    ]

    VENDOR_TYPES = [
        ('wholesaler', 'Wholesaler'),
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
    ]

    RISK_TIER_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
        null=True,
        blank=True,
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_tier = models.CharField(max_length=20, choices=RISK_TIER_CHOICES, default='Medium')

    vendor_type = models.CharField(max_length=50, choices=VENDOR_TYPES, default='wholesaler')
    country = models.CharField(max_length=100, default='United States')
    registration_number = models.CharField(max_length=100, blank=True)
    stock_symbol = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    internal_rep = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='represented_vendors',
    )
    relationship_start_date = models.DateField(default=date.today)

    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = VendorQuerySet.as_manager()

    def clean(self):
        if self.status == 'verified':
            if not self.pk:
                raise ValidationError('Cannot verify a new vendor. Create, add certs, then verify.')
            approved_valid_certs = self.certs.filter(
                expiry_date__gte=date.today(),
                is_current=True,
                approval_status='approved',
            )
            if not approved_valid_certs.exists():
                raise ValidationError('Cannot verify vendor without at least one approved valid certification.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CertificationQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser or user.is_staff:
            return self
        return self.filter(vendor__user=user)


class Certification(models.Model):
    CERT_TYPES = [
        ('ISO', 'ISO'),
        ('FDA', 'FDA'),
        ('CE', 'CE'),
    ]
    APPROVAL_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='certs')
    cert_type = models.CharField(max_length=50, choices=CERT_TYPES)
    file = models.FileField(upload_to=hashed_upload_path)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    is_current = models.BooleanField(default=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notified_30_days = models.BooleanField(default=False)
    notified_15_days = models.BooleanField(default=False)
    notified_1_day = models.BooleanField(default=False)

    objects = CertificationQuerySet.as_manager()

    def clean(self):
        if self.issue_date and self.expiry_date and self.expiry_date <= self.issue_date:
            raise ValidationError('Expiry date must be in the future relative to issue date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.expiry_date >= date.today() and self.is_current and self.approval_status == 'approved'

    def __str__(self):
        return f'{self.vendor.name} - {self.cert_type}'


class ContractQuerySet(models.QuerySet):
    def active(self, on_date=None):
        active_date = on_date or timezone.now().date()
        return self.filter(start_date__lte=active_date, end_date__gte=active_date)

    def with_is_active(self, on_date=None):
        active_date = on_date or timezone.now().date()
        return self.annotate(
            is_active=Case(
                When(Q(start_date__lte=active_date) & Q(end_date__gte=active_date), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def for_user(self, user):
        if user.is_superuser or user.is_staff:
            return self
        return self.filter(vendor__user=user)


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='contracts')
    contract_id = models.CharField(max_length=100)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    objects = ContractQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(end_date__gte=models.F('start_date')), name='contract_end_on_or_after_start'),
            models.UniqueConstraint(fields=['vendor', 'contract_id'], name='uniq_contract_id_per_vendor'),
        ]
        indexes = [models.Index(fields=['start_date', 'end_date'])]

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('Contract end date cannot be earlier than start date.')

    @property
    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.contract_id} ({self.vendor.name})'


class ProductQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser or user.is_staff:
            return self
        return self.filter(vendor__user=user)


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

    objects = ProductQuerySet.as_manager()
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
        return f'{self.vendor.name} changed to {self.status} at {self.timestamp}'
