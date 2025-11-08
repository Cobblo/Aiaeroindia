# orders/models.py
from django.db import models
from django.contrib.auth.models import User
from accounts.models import Address          # ✅ reuse the accounts Address
from catalog.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    # keep nullable during migration to avoid prompts; you can tighten later
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders",
        null=True, blank=True
    )
    email = models.EmailField()

    address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="orders",
        null=True, blank=True
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    razorpay_order_id = models.CharField(max_length=100, blank=True, default="")
    payment_id        = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product  = models.ForeignKey(Product, on_delete=models.PROTECT)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product} x {self.quantity}"
