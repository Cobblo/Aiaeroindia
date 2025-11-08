from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import TeamMember

class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "role", "skills")
    list_filter = ("is_active",)
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 5, "cols": 80})},
    }

admin.site.register(TeamMember, TeamMemberAdmin)   # ✅ explicit registration
