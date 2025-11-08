from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    # /products/  -> product list
    path("", views.product_list, name="product_list"),

    # /products/category/<category-slug>/
    path("category/<slug:category_slug>/", views.product_list, name="category"),

    # /products/<product-slug>/
    path("<slug:slug>/", views.product_detail, name="product_detail"),
]
