# blog/admin.py
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # List page columns
    list_display  = ("title", "is_published", "created_at")
    list_filter   = ("is_published", "created_at")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Content", {
            "fields": (
                "title",
                "slug",
                "excerpt",
                "image",        # 👈 NEW: image upload field
                "content",
                "is_published",
            )
        }),
        ("YouTube", {
            "description": "Safer default is thumbnail. Turn on embed only if the video allows embedding.",
            "fields": (
                "youtube_url",
                "youtube_id",
                "youtube_embed_url",
                "show_embed_player",
            ),
        }),
        ("Meta", {
            "fields": ("created_at",),
        }),
    )

    # Read-only fields in admin
    readonly_fields = ("created_at", "youtube_id", "youtube_embed_url")
