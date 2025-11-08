from decimal import Decimal, ROUND_HALF_UP
import base64
from typing import List, Dict, Optional

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from django.conf import settings

from core.utils.pdf import render_pdf_from_template


def _read_logo_b64(static_path: str) -> Optional[str]:
    fs_path = finders.find(static_path)
    if not fs_path:
        print(f"[WARN] Logo not found at static path: {static_path}")
        return None
    try:
        with open(fs_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception as e:
        print(f"[WARN] Failed to read logo: {e}")
        return None


def _normalize_items(order) -> List[Dict[str, str]]:
    rel = getattr(order, "items", None)
    rows = rel.all() if hasattr(rel, "all") else (rel or [])
    out: List[Dict[str, str]] = []
    for i in rows:
        name = getattr(getattr(i, "product", None), "name", "") or getattr(i, "name", "Item")
        qty = int(getattr(i, "quantity", 0) or 0)
        price_raw = getattr(i, "price", None)
        if price_raw is None:
            price_raw = getattr(getattr(i, "product", None), "price", None)
        try:
            price = Decimal(price_raw or 0)
        except Exception:
            price = Decimal("0.00")
        total_raw = getattr(i, "total", None)
        try:
            line_total = Decimal(total_raw) if total_raw is not None else (price * Decimal(qty))
        except Exception:
            line_total = price * Decimal(qty)
        out.append({
            "name": str(name),
            "qty": str(qty),
            "price": f"{price:.2f}",
            "line_total": f"{line_total:.2f}",
        })
    return out


def _q(x) -> Decimal:
    try:
        return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def send_order_confirmation_with_invoice(order, to_email: str, request=None):
    """
    Send HTML + text confirmation and attach a PDF built from invoices/invoice_v2.html.
    Customer + aiaero44@gmail.com both receive it.
    """
    subject = f"Thank you! Order #{order.id} received"

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "info@aiaeroindia.com")

    # 👇 both addresses will receive the same mail + PDF
    to = [to_email, "aiaero44@gmail.com"]

    logo_b64 = _read_logo_b64("assets/img/Aiaero_logo.png")
    line_items = _normalize_items(order)

    subtotal = _q(getattr(order, "subtotal", 0))
    tax      = _q(getattr(order, "tax", 0))
    shipping = _q(getattr(order, "shipping", 0))
    total    = _q(getattr(order, "total", 0))
    tax_rate_pct = str(getattr(settings, "CHECKOUT_TAX_RATE_PCT", "18"))

    ctx = {
        "order": order,
        "items": line_items,
        "line_items": line_items,
        "company_logo_b64": logo_b64,
        "company_name": "Ai-Aero India Pvt Ltd",
        "company_email": "info@aiaeroindia.com",
        "subtotal": subtotal, "subtotal_str": f"{subtotal:.2f}",
        "tax": tax,           "tax_str": f"{tax:.2f}",
        "shipping": shipping, "shipping_str": f"{shipping:.2f}",
        "total": total,       "total_str": f"{total:.2f}",
        "tax_rate_pct": tax_rate_pct,
    }

    html_body = render_to_string("emails/order_confirmation.html", ctx)
    text_body = render_to_string("emails/order_confirmation.txt", ctx)

    msg = EmailMultiAlternatives(subject, text_body, from_email, to)
    msg.attach_alternative(html_body, "text/html")

    try:
        pdf_bytes = render_pdf_from_template("invoices/invoice_v2.html", ctx)
        if pdf_bytes:
            msg.attach(f"invoice-{order.id}.pdf", pdf_bytes, "application/pdf")
        else:
            print(f"[WARN] render_pdf_from_template returned empty bytes for order #{order.id}")
    except Exception as e:
        print(f"[WARN] PDF generation failed for order #{order.id}: {e}")

    msg.send(fail_silently=False)
