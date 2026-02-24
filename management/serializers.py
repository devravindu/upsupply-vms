from rest_framework import serializers

from .models import Certification, Contract, Product, Vendor


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'status', 'contact_name', 'contact_email', 'contact_phone', 'website']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'vendor', 'name', 'status']


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id', 'vendor', 'cert_type', 'issue_date', 'expiry_date', 'is_current', 'approval_status']


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'vendor', 'contract_id', 'total_value', 'start_date', 'end_date']
