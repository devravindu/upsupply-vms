from datetime import date

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Certification, Vendor, VendorHistory


def _refresh_vendor_status(vendor):
    approved_valid_certs = vendor.certs.filter(
        expiry_date__gte=date.today(),
        is_current=True,
        approval_status='approved',
    )
    pending_review = vendor.certs.filter(approval_status='pending').exists()

    if approved_valid_certs.exists() and vendor.status != 'verified':
        vendor.status = 'verified'
        vendor.save()
    elif vendor.status == 'verified' and not approved_valid_certs.exists():
        vendor.status = 'inactive'
        vendor.risk_tier = 'High'
        vendor.save()
    elif not approved_valid_certs.exists() and pending_review and vendor.status not in {'under_review', 'inactive'}:
        vendor.status = 'under_review'
        vendor.save()


@receiver(post_save, sender=Certification)
@receiver(post_delete, sender=Certification)
def update_vendor_status(sender, instance, **kwargs):
    _refresh_vendor_status(instance.vendor)


@receiver(pre_save, sender=Vendor)
def track_vendor_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Vendor.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                user = getattr(instance, '_current_user', None)
                VendorHistory.objects.create(vendor=instance, status=instance.status, changed_by=user)
        except Vendor.DoesNotExist:
            pass


@receiver(post_save, sender=Vendor)
def track_vendor_creation(sender, instance, created, **kwargs):
    if created:
        user = getattr(instance, '_current_user', None)
        VendorHistory.objects.create(vendor=instance, status=instance.status, changed_by=user)
