from rest_framework import viewsets

from .models import Certification, Contract, Product, Vendor
from .serializers import CertificationSerializer, ContractSerializer, ProductSerializer, VendorSerializer


class ScopedModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.queryset.for_user(self.request.user)


class VendorViewSet(ScopedModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


class ProductViewSet(ScopedModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CertificationViewSet(ScopedModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer


class ContractViewSet(ScopedModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
