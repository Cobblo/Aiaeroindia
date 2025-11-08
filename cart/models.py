from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product

class CartItem(models.Model):
    user        = models.ForeignKey(User, null=True, blank=True,
                                    on_delete=models.CASCADE,
                                    related_name="cart_items")
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    product     = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity    = models.PositiveIntegerField(default=1)
    added_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        # You can add uniqueness if you want to prevent dup rows
        # unique_together = (("user", "product"), ("session_key", "product"))
        indexes = [models.Index(fields=["user"]), models.Index(fields=["session_key"])]

    def __str__(self):
        who = self.user.username if self.user_id else self.session_key
        return f"{who} - {self.product} x {self.quantity}"
