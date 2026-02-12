from django import forms
from .models import Vendor, Certification

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name']

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['cert_type', 'file', 'issue_date', 'expiry_date']
