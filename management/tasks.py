from datetime import date

try:
    from celery import shared_task
except ModuleNotFoundError:
    def shared_task(func):
        return func
from django.core.mail import send_mail

from .models import Certification, Vendor


@shared_task
def run_daily_certification_checks():
    today = date.today()

    for cert in Certification.objects.select_related('vendor', 'vendor__internal_rep').filter(is_current=True):
        days_until_expiry = (cert.expiry_date - today).days
        recipients = [email for email in [cert.vendor.contact_email, getattr(cert.vendor.internal_rep, 'email', None)] if email]

        if days_until_expiry == 30 and not cert.notified_30_days:
            _send_expiry_notice(cert, recipients, 30)
            cert.notified_30_days = True
            cert.save(update_fields=['notified_30_days'])
        elif days_until_expiry == 15 and not cert.notified_15_days:
            _send_expiry_notice(cert, recipients, 15)
            cert.notified_15_days = True
            cert.save(update_fields=['notified_15_days'])
        elif days_until_expiry == 1 and not cert.notified_1_day:
            _send_expiry_notice(cert, recipients, 1)
            cert.notified_1_day = True
            cert.save(update_fields=['notified_1_day'])

    # auto-inactivate verified vendors with no approved, unexpired certs
    verified_vendors = Vendor.objects.filter(status='verified')
    for vendor in verified_vendors:
        has_approved_valid = vendor.certs.filter(
            expiry_date__gte=today,
            is_current=True,
            approval_status='approved',
        ).exists()
        if not has_approved_valid:
            vendor.status = 'inactive'
            vendor.save(update_fields=['status'])


def _send_expiry_notice(cert, recipients, days_remaining):
    if not recipients:
        return
    send_mail(
        subject=f'Certification expiry alert: {days_remaining} day(s) remaining',
        message=(
            f'Certification {cert.cert_type} for vendor {cert.vendor.name} '
            f'expires on {cert.expiry_date}. Please upload and review renewal documents.'
        ),
        from_email=None,
        recipient_list=recipients,
        fail_silently=True,
    )
