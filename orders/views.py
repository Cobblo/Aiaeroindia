# orders/views.py
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import Address
from cart.cart import Cart
from .models import Order, OrderItem
from .utils import calculate_totals, calculate_totals_from_items


def _order_totals_context(order: Order):
    """
    Return a dict with subtotal, shipping, tax, total, tax_rate_pct.
    If the Order already stored them, use them; otherwise recompute from items.
    """
    have_all = (order.subtotal is not None) and (order.tax is not None) and (order.total is not None)
    if have_all:
        return {
            "subtotal": order.subtotal,
            "shipping": order.shipping or Decimal("0.00"),
            "tax": order.tax,
            "total": order.total,
            # tax_rate_pct is only shown as a label; keep your default from utils
            "tax_rate_pct": calculate_totals_from_items([])["tax_rate_pct"],
        }

    # Recompute from OrderItems (covers legacy orders or if fields were null)
    items = OrderItem.objects.filter(order=order)
    return calculate_totals_from_items(items)


@login_required
def checkout(request):
    cart = Cart(request)

    cart_count = cart.count() if callable(getattr(cart, "count", None)) else getattr(cart, "count", 0)
    if int(cart_count or 0) == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "id")
    default_address = addresses.first()
    if not default_address:
        messages.warning(request, "Please add a shipping address first.")
        return redirect("/accounts/profile/?edit=1")

    totals = calculate_totals(cart)

    if request.method == "POST":
        addr_id = request.POST.get("address_id") or str(default_address.id)
        address = get_object_or_404(Address, id=addr_id, user=request.user)

        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            address=address,
            subtotal=totals["subtotal"],
            shipping=totals["shipping"],
            tax=totals["tax"],
            total=totals["total"],
        )

        for row in cart:
            product = row.get("product") if isinstance(row, dict) else getattr(row, "product", None)
            if product is None:
                continue
            try:
                qty = int(row.get("qty", 1) if isinstance(row, dict) else getattr(row, "qty", 1))
            except (TypeError, ValueError):
                qty = 1
            qty = max(1, qty)
            price = getattr(product, "price", 0)

            OrderItem.objects.create(order=order, product=product, price=price, quantity=qty)

            if hasattr(product, "stock") and product.stock is not None:
                try:
                    product.stock = max(0, int(product.stock) - qty)
                    product.save(update_fields=["stock"])
                except (TypeError, ValueError):
                    pass

        request.session["current_order_id"] = order.id
        return redirect("payments:pay")

    context = {
        "cart": cart,
        "addresses": addresses,
        "selected_address_id": default_address.id,
        "cart_subtotal": totals["subtotal"],
        "tax": totals["tax"],
        "shipping": totals["shipping"],
        "total": totals["total"],
        "tax_rate_pct": totals.get("tax_rate_pct"),
        "ship_free_over": totals.get("free_over"),
        "ship_flat": totals.get("ship_flat"),
    }
    return render(request, "orders/checkout.html", context)


@login_required
def my_orders(request):
    orders = list(Order.objects.filter(user=request.user).order_by("-created_at"))
    if not orders:
        return render(request, "orders/my_orders.html", {"orders": []})

    order_map = {o.id: o for o in orders}
    for o in orders:
        setattr(o, "item_list", [])

    items = OrderItem.objects.filter(order_id__in=order_map.keys()).select_related("product")
    for it in items:
        order_map[it.order_id].item_list.append(it)

    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related("product")

    # Ensure the template always gets the breakdown
    totals_ctx = _order_totals_context(order)

    ctx = {
        "order": order,
        "items": items,
        "subtotal": totals_ctx["subtotal"],
        "shipping": totals_ctx["shipping"],
        "tax": totals_ctx["tax"],
        "total": totals_ctx["total"],
        "tax_rate_pct": totals_ctx["tax_rate_pct"],
    }
    return render(request, "orders/order_detail.html", ctx)
