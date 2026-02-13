from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Certification, Vendor, VendorHistory

@receiver(post_save, sender=Certification)
@receiver(post_delete, sender=Certification)
def update_vendor_status(sender, instance, **kwargs):
    vendor = instance.vendor

    # Check if we need to auto-invalidate
    if vendor.status == 'verified':
        valid_certs = vendor.certs.filter(expiry_date__gte=timezone.now().date(), is_current=True)
        if not valid_certs.exists():
            vendor.status = 'inactive'
            # We can save without user for system updates?
            # Or should we attribute it to system?
            # If changed_by is null, it might imply system.
            vendor.save()

@receiver(pre_save, sender=Vendor)
def track_vendor_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Vendor.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed
                user = getattr(instance, '_current_user', None)
                VendorHistory.objects.create(
                    vendor=instance,
                    status=instance.status,
                    changed_by=user
                )
        except Vendor.DoesNotExist:
            pass
    else:
        # New vendor
        user = getattr(instance, '_current_user', None)
        # We can't create VendorHistory here because Vendor instance is not saved yet (no PK).
        # We must use post_save for new instances.
        pass

@receiver(post_save, sender=Vendor)
def track_vendor_creation(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance, '_current_user', None)
        VendorHistory.objects.create(
            vendor=instance,
            status=instance.status,
            changed_by=user
        )

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date
from .models import Certification, Vendor, VendorHistory

@receiver(post_save, sender=Certification)
@receiver(post_delete, sender=Certification)
def update_vendor_status(sender, instance, **kwargs):
    vendor = instance.vendor

    # Check if we need to auto-invalidate
    if vendor.status == 'verified':
        valid_certs = vendor.certs.filter(expiry_date__gte=date.today(), is_current=True)
        if not valid_certs.exists():
            vendor.status = 'inactive'
            vendor.save()

@receiver(pre_save, sender=Vendor)
def track_vendor_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Vendor.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed
                user = getattr(instance, '_current_user', None)
                VendorHistory.objects.create(
                    vendor=instance,
                    status=instance.status,
                    changed_by=user
                )
        except Vendor.DoesNotExist:
            pass
    else:
        # New vendor
        user = getattr(instance, '_current_user', None)
        # We can't create VendorHistory here because Vendor instance is not saved yet (no PK).
        # We must use post_save for new instances.
        pass

@receiver(post_save, sender=Vendor)
def track_vendor_creation(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance, '_current_user', None)
        VendorHistory.objects.create(
            vendor=instance,
            status=instance.status,
            changed_by=user
        )
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Certification, Vendor, VendorHistory

@receiver(post_save, sender=Certification)
@receiver(post_delete, sender=Certification)
def update_vendor_status(sender, instance, **kwargs):
    vendor = instance.vendor
    # Auto-invalidate if no valid certs exist
    if vendor.status == 'verified':
        valid_certs = vendor.certs.filter(expiry_date__gte=timezone.now().date(), is_current=True)
        if not valid_certs.exists():
            vendor.status = 'inactive'
            vendor.save()

@receiver(pre_save, sender=Vendor)
def track_vendor_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Vendor.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                user = getattr(instance, '_current_user', None)
                VendorHistory.objects.create(
                    vendor=instance,
                    status=instance.status,
                    changed_by=user
                )
        except Vendor.DoesNotExist:
            pass

@receiver(post_save, sender=Vendor)
def track_vendor_creation(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance, '_current_user', None)
        VendorHistory.objects.create(
            vendor=instance,
            status=instance.status,
            changed_by=user
        )