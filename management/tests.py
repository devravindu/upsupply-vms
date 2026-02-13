from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Vendor, Certification, Product, VendorHistory
from datetime import timedelta, date
import uuid

class VendorLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor_user', password='password')
        self.vendor = Vendor.objects.create(name="Test Vendor", user=self.user)
        self.file = SimpleUploadedFile("test_cert.pdf", b"file_content", content_type="application/pdf")

    def test_vendor_verification_constraint(self):
        """Test that a vendor cannot be verified without a valid certification."""
        # Try to verify without any certs
        self.vendor.status = 'verified'
        with self.assertRaises(ValidationError):
            self.vendor.save()

        # Add an expired certification (issue date long ago)
        Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today() - timedelta(days=365*2),
            expiry_date=date.today() - timedelta(days=1),
            is_current=True
        )

        # Try to verify again
        self.vendor.status = 'verified'
        with self.assertRaises(ValidationError):
            self.vendor.save()

        # Add a valid certification
        Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )

        # Now verification should succeed
        self.vendor.status = 'verified'
        self.vendor.save()
        self.assertEqual(self.vendor.status, 'verified')

    def test_auto_invalidation_on_delete(self):
        """Test that vendor status switches to inactive if valid cert is deleted."""
        # Setup verified vendor
        cert = Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )
        self.vendor.status = 'verified'
        self.vendor.save()

        # Delete the cert
        cert.delete()

        # Refresh vendor
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.status, 'inactive')

    def test_auto_invalidation_on_update(self):
        """Test that vendor status switches to inactive if cert expires/invalidated."""
        # Setup verified vendor with past issue date
        issue_date = date.today() - timedelta(days=400)
        cert = Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=issue_date,
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )
        self.vendor.status = 'verified'
        self.vendor.save()

        # Update cert to be expired
        cert.expiry_date = date.today() - timedelta(days=1)
        cert.save()

        # Refresh vendor
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.status, 'inactive')

        # Reset vendor to verified with valid cert
        cert.expiry_date = date.today() + timedelta(days=365)
        cert.save()
        self.vendor.status = 'verified'
        self.vendor.save()

        # Update cert to be not current
        cert.is_current = False
        cert.save()

        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.status, 'inactive')

    def test_certification_validation(self):
        """Test expiry date validation."""
        with self.assertRaises(ValidationError):
            Certification.objects.create(
                vendor=self.vendor,
                cert_type='ISO',
                file=self.file,
                issue_date=date.today(),
                expiry_date=date.today(), # Same day invalid? Logic: expiry <= issue
            )

    def test_product_visibility(self):
        """Test Product visibility rule."""
        # Create product
        product = Product.objects.create(vendor=self.vendor, name="Test Product", status='active')

        # Vendor pending
        self.assertFalse(product.is_active)
        self.assertFalse(Product.active_objects.filter(pk=product.pk).exists())

        # Verify vendor
        Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )
        self.vendor.status = 'verified'
        self.vendor.save()

        self.assertTrue(product.is_active)
        self.assertTrue(Product.active_objects.filter(pk=product.pk).exists())

        # Invalidate vendor
        self.vendor.status = 'inactive'
        self.vendor.save()

        self.assertFalse(product.is_active)
        self.assertFalse(Product.active_objects.filter(pk=product.pk).exists())

    def test_hashed_filename(self):
        """Test that uploaded files have hashed filenames."""
        cert = Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )
        self.assertNotEqual(cert.file.name, 'certs/test_cert.pdf')
        self.assertTrue(cert.file.name.startswith('certs/'))
        self.assertTrue(cert.file.name.endswith('.pdf'))
        # Should be a hex string (uuid4)
        filename = cert.file.name.split('/')[-1].split('.')[0]
        try:
            uuid.UUID(filename)
        except ValueError:
            self.fail(f"Filename {filename} is not a valid UUID")

    def test_audit_trail(self):
        """Test VendorHistory creation."""
        # Initial create -> pending. History created?
        # My implementation: post_save on created creates history.
        history = VendorHistory.objects.filter(vendor=self.vendor).order_by('timestamp')
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().status, 'pending')

        # Change status
        self.vendor._current_user = self.user
        # Need a valid cert to verify
        Certification.objects.create(
            vendor=self.vendor,
            cert_type='ISO',
            file=self.file,
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            is_current=True
        )
        self.vendor.status = 'verified'
        self.vendor.save()

        history = VendorHistory.objects.filter(vendor=self.vendor).order_by('timestamp')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history.last().status, 'verified')
        self.assertEqual(history.last().changed_by, self.user)

class VendorFieldsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor_rep', password='password')
        self.vendor = Vendor.objects.create(
            name="New Vendor",
            vendor_type='manufacturer',
            country='Germany',
            registration_number='DE123456',
            stock_symbol='NVDR',
            website='https://newvendor.com',
            internal_rep=self.user,
            contact_name='Hans Mueller',
            contact_email='hans@newvendor.com',
            contact_phone='+49123456789',
            total_spend=1000.50
        )

    def test_vendor_fields_storage(self):
        """Test that new fields are stored and retrieved correctly."""
        vendor = Vendor.objects.get(pk=self.vendor.pk)
        self.assertEqual(vendor.vendor_type, 'manufacturer')
        self.assertEqual(vendor.country, 'Germany')
        self.assertEqual(vendor.registration_number, 'DE123456')
        self.assertEqual(vendor.stock_symbol, 'NVDR')
        self.assertEqual(vendor.website, 'https://newvendor.com')
        self.assertEqual(vendor.internal_rep, self.user)
        self.assertEqual(vendor.contact_name, 'Hans Mueller')
        self.assertEqual(vendor.contact_email, 'hans@newvendor.com')
        self.assertEqual(vendor.contact_phone, '+49123456789')
        self.assertEqual(vendor.total_spend, 1000.50)

    def test_default_values(self):
        """Test default values for new fields."""
        vendor = Vendor.objects.create(name="Default Vendor")
        self.assertEqual(vendor.vendor_type, 'wholesaler')
        self.assertEqual(vendor.country, 'United States')
        self.assertEqual(vendor.total_spend, 0.00)
        self.assertEqual(vendor.relationship_start_date, date.today())
