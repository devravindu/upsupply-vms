from django import forms

from .models import Certification, Vendor


TAILWIND_INPUT = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'


class VendorForm(forms.ModelForm):
    registration_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'e.g. EL1002022'}))

    class Meta:
        model = Vendor
        fields = [
            'name',
            'vendor_type',
            'status',
            'risk_tier',
            'country',
            'registration_number',
            'stock_symbol',
            'website',
            'internal_rep',
            'relationship_start_date',
            'contact_name',
            'contact_email',
            'contact_phone',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'vendor_type': forms.Select(attrs={'class': TAILWIND_INPUT}),
            'status': forms.Select(attrs={'class': TAILWIND_INPUT}),
            'risk_tier': forms.Select(attrs={'class': TAILWIND_INPUT}),
            'country': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'stock_symbol': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'website': forms.URLInput(attrs={'class': TAILWIND_INPUT}),
            'internal_rep': forms.Select(attrs={'class': TAILWIND_INPUT}),
            'relationship_start_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'contact_email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
        }


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['contact_name', 'contact_email', 'contact_phone', 'website']
        widgets = {
            'contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'contact_email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'website': forms.URLInput(attrs={'class': TAILWIND_INPUT}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['cert_type', 'file', 'issue_date', 'expiry_date', 'is_current']
        widgets = {
            'cert_type': forms.Select(attrs={'class': TAILWIND_INPUT}),
            'issue_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }
