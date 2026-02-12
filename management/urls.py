from django.urls import path
from .views import VendorProfileView, CertificationUploadView

urlpatterns = [
    path('profile/', VendorProfileView.as_view(), name='vendor_profile'),
    path('profile/upload_cert/', CertificationUploadView.as_view(), name='cert_upload'),
]
