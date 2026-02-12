from django.views.generic import UpdateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .models import Vendor, Certification
from .forms import VendorForm, CertificationForm

class VendorProfileView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'management/vendor_profile.html'
    success_url = reverse_lazy('vendor_profile')

    def get_object(self, queryset=None):
        # Assumes user has a vendor_profile related object
        # If user is admin/superuser without vendor profile, this will crash.
        # But this view is for vendors.
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
