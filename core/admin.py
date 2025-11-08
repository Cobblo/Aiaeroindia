from django.contrib import admin
from .models import PromoVideo

@admin.register(PromoVideo)
class PromoVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "sort_order", "created_at")
    list_editable = ("is_active", "sort_order")
    search_fields = ("title", "subtitle", "youtube_url")
    list_filter = ("is_active",)
