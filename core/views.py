from django.shortcuts import render
from catalog.models import Product
from core.models import PromoVideo
from team.models import TeamMember  # ⬅️ pull team from admin

def home(request):
    featured = (
        Product.objects
        .filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )
    videos = (
        PromoVideo.objects.filter(is_active=True)
        .order_by("sort_order", "-created_at")
    )
    team_members = (
        TeamMember.objects.filter(is_active=True)
        .order_by("sort_order", "name")
    )

    return render(request, "index.html", {
        "featured_products": featured,
        "videos": videos,
        "team_members": team_members,   # ⬅️ to template
    })

def soft(request):
    return render(request, "soft.html")

def hard(request):
    return render(request, "hard.html")
