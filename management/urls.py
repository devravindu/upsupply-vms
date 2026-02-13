from django.urls import path
from .views import (
    DashboardView, VendorListView, VendorDetailView,
    VendorCreateView, VendorUpdateView, VendorProfileView,
    CertificationUploadView
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('vendors/', VendorListView.as_view(), name='vendor_list'),
    path('vendors/create/', VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<uuid:pk>/', VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/<uuid:pk>/edit/', VendorUpdateView.as_view(), name='vendor_update'),

    # Original Vendor Profile URLs (might be redundant now but keeping for compatibility if vendor user logs in)
    path('profile/', VendorProfileView.as_view(), name='vendor_profile'),
    path('profile/upload_cert/', CertificationUploadView.as_view(), name='cert_upload'),
]
