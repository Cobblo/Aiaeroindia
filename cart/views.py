# cart/views.py
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .cart import Cart
from .models import CartItem
from catalog.models import Product

# --- config ---
TAX_RATE = Decimal("0.18")
SHIP_FLAT = Decimal(getattr(settings, "CART_SHIPPING_FLAT", "100.00"))
SHIP_FREE_OVER = Decimal(getattr(settings, "CART_SHIPPING_FREE_OVER", "9999.00"))


def _next_url(request, fallback="core:home"):
    return (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse(fallback)
    )


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _save_db_cart_row(request, product, qty, update=False):
    if request.user.is_authenticated:
        row, created = CartItem.objects.get_or_create(
            user=request.user, product=product, defaults={"quantity": qty}
        )
    else:
        sk = _ensure_session_key(request)
        row, created = CartItem.objects.get_or_create(
            session_key=sk, product=product, defaults={"quantity": qty}
        )

    if not created:
        row.quantity = qty if update else (row.quantity + qty)
    row.quantity = max(1, row.quantity)
    row.save()


def _delete_db_cart_row(request, product):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user, product=product).delete()
    else:
        sk = request.session.session_key
        if sk:
            CartItem.objects.filter(session_key=sk, product=product).delete()


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = Cart(request)

    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, qty)

    cart.add(product_id, qty=qty)
    _save_db_cart_row(request, product, qty, update=False)

    return redirect(_next_url(request))


@require_POST
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = Cart(request)
    cart.remove(product_id)
    _delete_db_cart_row(request, product)
    return redirect(_next_url(request, fallback="cart:view"))


@require_POST
def update_qty(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = Cart(request)

    store = request.session.get("cart", {})
    key = str(product_id)
    current_qty = int(store.get(key, {}).get("qty", 0))

    try:
        delta = int(request.POST.get("delta", 0))
    except (TypeError, ValueError):
        delta = 0

    if delta != 0:
        new_qty = max(1, current_qty + delta)
    else:
        try:
            new_qty = int(request.POST.get("quantity", current_qty or 1))
        except (TypeError, ValueError):
            new_qty = current_qty or 1
        new_qty = max(1, new_qty)

    cart.add(product_id, qty=new_qty, update=True)
    _save_db_cart_row(request, product, new_qty, update=True)

    return redirect(_next_url(request, fallback="cart:view"))


@login_required
@require_POST
def clear_cart(request):
    request.session["cart"] = {}
    request.session.modified = True
    CartItem.objects.filter(user=request.user).delete()
    return redirect(_next_url(request, fallback="cart:view"))


def view_cart(request):
    """Render the cart with subtotal, tax, shipping, and grand total."""
    cart = Cart(request)

    # hydrate from DB if session empty
    if request.user.is_authenticated:
        qs = CartItem.objects.filter(user=request.user).select_related("product")
    else:
        sk = request.session.session_key
        if not sk:
            request.session.create()
            sk = request.session.session_key
        qs = CartItem.objects.filter(session_key=sk).select_related("product")

    if not request.session.get("cart") and qs.exists():
        for row in qs:
            cart.add(row.product_id, qty=row.quantity, update=True)
        request.session.modified = True

    # totals
    subtotal = Decimal("0.00")
    for item in cart:
        subtotal += Decimal(item["price"]) * Decimal(item["qty"])

    tax_amount = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    if subtotal >= SHIP_FREE_OVER:
        shipping_amount = Decimal("0.00")
        shipping_free_note = f"free over ₹{SHIP_FREE_OVER.quantize(Decimal('0.00'))}"
    else:
        shipping_amount = SHIP_FLAT
        shipping_free_note = ""

    grand_total = (subtotal + tax_amount + shipping_amount).quantize(Decimal("0.01"))

    return render(
        request,
        "cart/view.html",
        {
            "cart": cart,
            "cart_total": subtotal,            # legacy
            "cart_subtotal": subtotal,
            "tax_rate_pct": (TAX_RATE * 100).quantize(Decimal("0.01")),
            "tax_amount": tax_amount,
            "shipping_amount": shipping_amount,
            "shipping_free_note": shipping_free_note,
            "grand_total": grand_total,
        },
    )
