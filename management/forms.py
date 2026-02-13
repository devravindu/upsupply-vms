from django import forms
from .models import Vendor, Certification

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'name', 'vendor_type', 'country', 'registration_number',
            'stock_symbol', 'website', 'contact_name', 'contact_email',
            'contact_phone'
        ]

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['cert_type', 'file', 'issue_date', 'expiry_date', 'is_current']