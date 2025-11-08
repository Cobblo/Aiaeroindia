# payments/views.py
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from orders.emails import send_order_confirmation_with_invoice


# ---- helper: clear the cart on success --------------------------------------
def _clear_cart(request):
    """Best-effort clear for both session-based and DB-based carts."""
    # Session cart (Cart class with clear())
    try:
        from cart.cart import Cart
        Cart(request).clear()
    except Exception:
        pass

    # DB cart items (if you have a CartItem model)
    try:
        if request.user.is_authenticated:
            from cart.models import CartItem
            # adapt the filter to your schema (ordered/checked_out flags etc.)
            CartItem.objects.filter(user=request.user).delete()
    except Exception:
        pass
# -----------------------------------------------------------------------------


def pay(request):
    order_id = request.session.get('current_order_id')
    order = get_object_or_404(Order, id=order_id, status='created')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    rzp_order = client.order.create(dict(
        amount=int(order.total * 100),
        currency='INR',
        payment_capture=1
    ))
    order.razorpay_order_id = rzp_order['id']
    order.save()

    context = {
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': rzp_order['id'],
        'amount_paise': int(order.total * 100),
        'currency': 'INR',
        'customer_name': order.address.full_name if getattr(order, "address", None) else '',
        'customer_email': getattr(order, "email", "") or getattr(getattr(order, "user", None), "email", ""),
        'customer_contact': getattr(order.address, "phone", "") if getattr(order, "address", None) else '',
    }
    return render(request, 'payments/pay.html', context)


@csrf_exempt
def verify(request):
    """
    Razorpay returns POST with: razorpay_order_id, razorpay_payment_id, razorpay_signature.
    On success:
      - mark order paid
      - clear cart
      - send confirmation email + attach PDF invoice
      - show success page
    """
    if request.method != 'POST':
        return redirect('core:home')

    params = {
        'razorpay_order_id': request.POST.get('razorpay_order_id'),
        'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
        'razorpay_signature': request.POST.get('razorpay_signature'),
    }

    order = get_object_or_404(Order, razorpay_order_id=params['razorpay_order_id'])

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        # raises SignatureVerificationError if invalid
        client.utility.verify_payment_signature(params)

        # mark paid, store payment id, clean up
        order.status = 'paid'
        order.payment_id = params['razorpay_payment_id'] or ''
        order.save(update_fields=['status', 'payment_id'])

        # ✅ CLEAR THE CART
        _clear_cart(request)

        # no longer need the “current order” pointer
        request.session.pop('current_order_id', None)

        # ✅ SEND EMAIL + PDF INVOICE (best-effort, non-fatal if it fails)
        try:
            # Try common places to read customer's email
            customer_email = (
                getattr(order, "email", None)
                or getattr(getattr(order, "user", None), "email", None)
                or getattr(getattr(order, "address", None), "email", None)
            )
            if customer_email:
                send_order_confirmation_with_invoice(order, customer_email)
        except Exception as e:
            # Don't break the success flow if email fails
            # You may swap this for logging
            print(f"[WARN] Failed to send order email/invoice for order #{order.id}: {e}")

        return render(request, 'payments/success.html', {'order': order})

    except razorpay.errors.SignatureVerificationError:
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        return render(request, 'payments/failed.html', {'order': order})
