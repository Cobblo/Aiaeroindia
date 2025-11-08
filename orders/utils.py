# orders/utils.py
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings

def _to_dec(x, default="0.00"):
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(default)

def _money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ---- global defaults pulled from settings (shared everywhere) ----
TAX_RATE_PCT = _to_dec(getattr(settings, "CHECKOUT_TAX_RATE_PCT", "18.00"))
FREE_OVER    = _to_dec(getattr(settings, "CART_SHIPPING_FREE_OVER", "9999.00"))
SHIP_FLAT    = _to_dec(getattr(settings, "CART_SHIPPING_FLAT", "100.00"))

def calculate_totals(cart):
    """
    Compute totals from a Cart (iterable of rows with product/qty).
    """
    subtotal = Decimal("0.00")
    items_count = 0

    for row in cart:
        product = row.get("product")
        qty     = _to_dec(row.get("qty", 1), "1")

        if product is not None and hasattr(product, "price"):
            price = _to_dec(getattr(product, "price"))
        else:
            price = _to_dec(row.get("price", "0.00"))

        subtotal += price * qty
        try:
            items_count += int(qty)
        except Exception:
            items_count += 1

    subtotal = _money(subtotal)

    # Shipping
    shipping = Decimal("0.00") if (subtotal > 0 and subtotal >= FREE_OVER) else SHIP_FLAT
    shipping = _money(shipping)

    # Tax on subtotal
    tax = _money(subtotal * TAX_RATE_PCT / Decimal("100"))

    total = _money(subtotal + shipping + tax)

    return {
        "items_count": items_count,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "tax_rate_pct": TAX_RATE_PCT,
        "free_over": FREE_OVER,
        "ship_flat": SHIP_FLAT,
    }

def calculate_totals_from_items(items):
    """
    Compute totals from an iterable of OrderItem objects (price, quantity).
    Mirrors calculate_totals(cart) so invoice/email match checkout.
    """
    subtotal = Decimal("0.00")
    items_count = 0

    for it in items:
        price = _to_dec(getattr(it, "price", 0))
        qty   = int(getattr(it, "quantity", 1) or 1)
        subtotal += price * qty
        items_count += qty

    subtotal = _money(subtotal)
    shipping = Decimal("0.00") if (subtotal > 0 and subtotal >= FREE_OVER) else SHIP_FLAT
    shipping = _money(shipping)
    tax = _money(subtotal * TAX_RATE_PCT / Decimal("100"))
    total = _money(subtotal + shipping + tax)

    return {
        "items_count": items_count,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "tax_rate_pct": TAX_RATE_PCT,
        "free_over": FREE_OVER,
        "ship_flat": SHIP_FLAT,
    }
