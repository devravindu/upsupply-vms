from django.contrib import admin
from django.utils.html import format_html
from .models import Vendor, Certification, Product, VendorHistory, Contract

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'status_tag', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)

    def status_tag(self, obj):
        color = 'red'
        if obj.status == 'verified':
            color = 'green'
        elif obj.status == 'pending':
            color = 'red' # As per prompt
        elif obj.status == 'inactive':
             color = 'red'

        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())

    status_tag.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        obj._current_user = request.user
        super().save_model(request, obj, form, change)

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'cert_type', 'expiry_date', 'is_current', 'is_valid_display')
    list_filter = ('cert_type', 'is_current')

    def is_valid_display(self, obj):
        return obj.is_valid
    is_valid_display.boolean = True
    is_valid_display.short_description = 'Is Valid'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'status', 'is_active_display')
    list_filter = ('status',)

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = 'Is Active in System'

@admin.register(VendorHistory)
class VendorHistoryAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'status', 'changed_by', 'timestamp')
    readonly_fields = ('vendor', 'status', 'changed_by', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_id', 'vendor', 'total_value', 'start_date', 'end_date', 'is_active_display')
    search_fields = ('contract_id', 'vendor__name')
    list_filter = ('start_date', 'end_date')

    def is_active_display(self, obj):
        return obj.is_active

    is_active_display.boolean = True
    is_active_display.short_description = 'Is Active'
