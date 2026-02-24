from django.urls import path

from .views import (
    ApprovalQueueView,
    ApproveCertificationView,
    CertificationUploadView,
    DashboardView,
    VendorAuditExportView,
    VendorCreateView,
    VendorDetailView,
    VendorListView,
    VendorProfileView,
    VendorUpdateView,
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('vendors/', VendorListView.as_view(), name='vendor_list'),
    path('vendors/create/', VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<uuid:pk>/', VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/<uuid:pk>/edit/', VendorUpdateView.as_view(), name='vendor_update'),
    path('vendors/<uuid:pk>/audit-export/', VendorAuditExportView.as_view(), name='vendor_audit_export'),
    path('compliance/queue/', ApprovalQueueView.as_view(), name='approval_queue'),
    path('compliance/certifications/<int:pk>/approve/', ApproveCertificationView.as_view(), name='approve_certification'),
    path('profile/', VendorProfileView.as_view(), name='vendor_profile'),
    path('profile/upload_cert/', CertificationUploadView.as_view(), name='cert_upload'),
]
