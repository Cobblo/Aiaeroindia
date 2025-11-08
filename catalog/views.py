from django.shortcuts import render, get_object_or_404
from .models import Product

def product_list(request):
    qs = (
        Product.objects.select_related("category")
        .prefetch_related("images")
        .filter(is_active=True)
        .order_by("-created_at")
    )
    return render(request, "catalog/product_list.html", {"products": qs})

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        slug=slug, is_active=True
    )
    return render(request, "catalog/product_detail.html", {"product": product})