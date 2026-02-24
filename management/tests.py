from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Certification, Product, Vendor, VendorHistory


class VendorLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor_user', password='password')
        self.staff = User.objects.create_user(username='staff', password='password', is_staff=True)
        self.vendor = Vendor.objects.create(name='Test Vendor', user=self.user, contact_email='vendor@example.com')
        self.file = SimpleUploadedFile('test_cert.pdf', b'file_content', content_type='application/pdf')

    def test_vendor_verification_requires_approved_certification(self):
        self.vendor.status = 'verified'
        with self.assertRaises(ValidationError):
            self.vendor.save()

        cert = Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True,
            approval_status='pending',
        )

        self.vendor.status = 'verified'
        with self.assertRaises(ValidationError):
            self.vendor.save()

        cert.approval_status = 'approved'
        cert.save()
        self.vendor.status = 'verified'
        self.vendor.save()
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.status, 'verified')

    def test_certification_validation(self):
        with self.assertRaises(ValidationError):
            Certification.objects.create(
                vendor=self.vendor,
                cert_type='ISO',
                file=self.file,
                issue_date=date.today(),
                expiry_date=date.today(),
            )

    def test_product_visibility(self):
        product = Product.objects.create(vendor=self.vendor, name='Test Product', status='active')
        self.assertFalse(product.is_active)

    def test_audit_trail(self):
        history = VendorHistory.objects.filter(vendor=self.vendor)
        self.assertEqual(history.count(), 1)

    def test_object_level_vendor_scope(self):
        other_user = User.objects.create_user(username='other', password='password')
        other_vendor = Vendor.objects.create(name='Other', user=other_user)
        self.assertNotIn(other_vendor, Vendor.objects.for_user(self.user))

    def test_manual_approval_queue_endpoint(self):
        cert = Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )
        self.client.login(username='staff', password='password')
        response = self.client.post(reverse('approve_certification', args=[cert.pk]))
        self.assertEqual(response.status_code, 302)
        cert.refresh_from_db()
        self.assertEqual(cert.approval_status, 'approved')
