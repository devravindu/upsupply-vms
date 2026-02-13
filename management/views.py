from django.views.generic import UpdateView, CreateView, ListView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from .models import Vendor, Certification, Product
from .forms import VendorForm, CertificationForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'management/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # KPI Data
        context['total_vendors'] = Vendor.objects.count()
        context['verified_vendors'] = Vendor.objects.filter(status='verified').count()

        thirty_days_future = timezone.now().date() + timedelta(days=30)
        context['expiring_certs'] = Certification.objects.filter(
            expiry_date__lte=thirty_days_future,
            expiry_date__gte=timezone.now().date()
        ).count()

        context['total_products'] = Product.objects.count()

        # Chart Data (Vendor Status)
        verified_count = context['verified_vendors']
        pending_count = Vendor.objects.filter(status='pending').count()
        inactive_count = Vendor.objects.filter(status='inactive').count()

        context['chart_labels'] = ['Verified', 'Pending', 'Inactive']
        context['chart_data'] = [verified_count, pending_count, inactive_count]

        return context

class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'management/vendor_list.html'
    context_object_name = 'vendors'

    def get_queryset(self):
        return Vendor.objects.all().order_by('-created_at')

class VendorDetailView(LoginRequiredMixin, DetailView):
    model = Vendor
    template_name = 'management/vendor_detail.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['certs'] = self.object.certs.all()
        return context

class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_form.html'
    success_url = reverse_lazy('vendor_list')

    def form_valid(self, form):
        # Assign current user as internal_rep if not set?
        # Or just save. The form handles fields.
        return super().form_valid(form)

class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_form.html'
    success_url = reverse_lazy('vendor_list')

class VendorProfileView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_profile.html'
    success_url = reverse_lazy('vendor_profile')

    def get_object(self, queryset=None):
        return self.request.user.vendor_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['certs'] = self.object.certs.all()
        context['cert_form'] = CertificationForm()
        return context

class CertificationUploadView(LoginRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'management/cert_upload.html'
    success_url = reverse_lazy('vendor_profile')

    def form_valid(self, form):
        form.instance.vendor = self.request.user.vendor_profile
        return super().form_valid(form)
