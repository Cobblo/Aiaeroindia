from django.contrib import admin
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'pincode', 'is_default')
    list_filter = ('state', 'is_default')
    search_fields = ('full_name', 'city', 'pincode', 'user__username')
