from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import CartItem

@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    # Ensure session key exists
    sk = request.session.session_key
    if not sk:
        request.session.create()
        sk = request.session.session_key

    anon_items = list(CartItem.objects.filter(session_key=sk))

    if not anon_items:
        return

    for item in anon_items:
        # If the user already has the same product, sum quantities
        existing = CartItem.objects.filter(user=user, product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
            item.delete()
        else:
            item.user = user
            item.session_key = None
            item.save()
