import importlib.util

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('vendor/', include('management.urls')),
    path('', RedirectView.as_view(url='/vendor/dashboard/', permanent=True)),
    path('dashboard/', RedirectView.as_view(url='/vendor/dashboard/', permanent=True)),
]

if importlib.util.find_spec('two_factor'):
    urlpatterns.insert(1, path('', include('two_factor.urls', 'two_factor')))

if importlib.util.find_spec('rest_framework'):
    from rest_framework.routers import DefaultRouter

    from management.api import CertificationViewSet, ContractViewSet, ProductViewSet, VendorViewSet

    router = DefaultRouter()
    router.register('vendors', VendorViewSet, basename='api-vendors')
    router.register('products', ProductViewSet, basename='api-products')
    router.register('certifications', CertificationViewSet, basename='api-certifications')
    router.register('contracts', ContractViewSet, basename='api-contracts')
    urlpatterns.insert(3, path('api/', include(router.urls)))
