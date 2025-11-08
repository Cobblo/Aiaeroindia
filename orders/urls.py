from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),  # keep your existing checkout
    path("my/", views.my_orders, name="my_orders"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
]
