import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import CertificationForm, VendorForm, VendorProfileForm
from .models import Certification, Contract, Product, Vendor, VendorHistory


class ScopedQuerysetMixin:
    model = None

    def get_queryset(self):
        return self.model.objects.for_user(self.request.user)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'management/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_scope = Vendor.objects.for_user(self.request.user)

        context['total_vendors'] = vendor_scope.count()
        context['verified_vendors'] = vendor_scope.filter(status='verified').count()

        thirty_days_future = timezone.now().date() + timedelta(days=30)
        context['expiring_certs'] = Certification.objects.for_user(self.request.user).filter(
            expiry_date__lte=thirty_days_future,
            expiry_date__gte=timezone.now().date(),
        ).count()

        context['total_products'] = Product.objects.for_user(self.request.user).count()

        today = timezone.now().date()
        active_contracts = Contract.objects.for_user(self.request.user).active(on_date=today)
        context['total_spend'] = active_contracts.aggregate(total=Sum('total_value'))['total'] or 0

        spend_by_risk = active_contracts.values('vendor__risk_tier').annotate(total=Sum('total_value'))
        spend_map = {row['vendor__risk_tier']: row['total'] for row in spend_by_risk}
        context['risk_labels'] = ['Low', 'Medium', 'High']
        context['risk_spend_data'] = [
            float(spend_map.get('Low', 0) or 0),
            float(spend_map.get('Medium', 0) or 0),
            float(spend_map.get('High', 0) or 0),
        ]

        context['chart_labels'] = ['Verified', 'Pending', 'Under Review', 'Inactive']
        context['chart_data'] = [
            context['verified_vendors'],
            vendor_scope.filter(status='pending').count(),
            vendor_scope.filter(status='under_review').count(),
            vendor_scope.filter(status='inactive').count(),
        ]
        return context


class VendorListView(LoginRequiredMixin, ScopedQuerysetMixin, ListView):
    model = Vendor
    template_name = 'management/vendor_list.html'
    context_object_name = 'vendors'

    def get_queryset(self):
        today = timezone.now().date()
        return super().get_queryset().annotate(
            active_contract_value=Sum(
                'contracts__total_value',
                filter=Q(contracts__start_date__lte=today, contracts__end_date__gte=today),
            )
        ).order_by('-created_at')


class VendorDetailView(LoginRequiredMixin, ScopedQuerysetMixin, DetailView):
    model = Vendor
    template_name = 'management/vendor_detail.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['certs'] = self.object.certs.all()
        context['contracts'] = self.object.contracts.with_is_active()
        return context


class VendorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_form.html'
    success_url = reverse_lazy('vendor_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class VendorUpdateView(LoginRequiredMixin, ScopedQuerysetMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_form.html'
    success_url = reverse_lazy('vendor_list')


class VendorProfileView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorProfileForm
    template_name = 'management/vendor_profile.html'
    success_url = reverse_lazy('vendor_profile')

    def get_object(self, queryset=None):
        try:
            return self.request.user.vendor_profile
        except Vendor.DoesNotExist as exc:
            raise Http404('Vendor profile not found for this user.') from exc

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['certs'] = self.object.certs.all()
        context['products'] = self.object.products.all()
        context['contracts'] = self.object.contracts.with_is_active()
        context['cert_form'] = CertificationForm()
        return context


class CertificationUploadView(LoginRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'management/cert_upload.html'
    success_url = reverse_lazy('vendor_profile')

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor_profile
        form.instance.approval_status = 'pending'
        return super().form_valid(form)


class ApprovalQueueView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Certification
    template_name = 'management/approval_queue.html'
    context_object_name = 'certifications'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        return Certification.objects.filter(approval_status='pending').select_related('vendor')


class ApproveCertificationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk):
        cert = get_object_or_404(Certification, pk=pk)
        cert.approval_status = 'approved'
        cert.reviewed_by = request.user
        cert.reviewed_at = timezone.now()
        cert.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at'])
        messages.success(request, 'Certification approved.')
        return redirect('approval_queue')


class VendorAuditExportView(LoginRequiredMixin, ScopedQuerysetMixin, View):
    model = Vendor

    def get(self, request, pk):
        vendor = get_object_or_404(self.get_queryset(), pk=pk)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="vendor_audit_{vendor.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['vendor', 'status', 'changed_by', 'timestamp'])
        for record in VendorHistory.objects.filter(vendor=vendor).select_related('changed_by').order_by('timestamp'):
            writer.writerow([
                vendor.name,
                record.status,
                record.changed_by.username if record.changed_by else '',
                record.timestamp.isoformat(),
            ])
        return response
