# orders/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from core.utils.pdf import render_pdf_from_template

def send_order_confirmation_with_invoice(order, to_email: str):
    """
    Sends an HTML confirmation email + attaches a PDF invoice.
    Expects 'order' to have: id, created_at, total, billing/shipping fields, items relation etc.
    Adjust field names as per your models.
    """

    subject = f"Thank you! Order #{order.id} received"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [to_email]

    # Build email HTML and plain text
    context = {
        "order": order,
        "items": getattr(order, "items", []),  # or order.items.all()
    }
    html_body = render_to_string("emails/order_confirmation.html", context)
    text_body = render_to_string("emails/order_confirmation.txt", context)

    msg = EmailMultiAlternatives(subject, text_body, from_email, to)
    msg.attach_alternative(html_body, "text/html")

    # Generate PDF invoice from template
    pdf_bytes = render_pdf_from_template("invoices/invoice.html", context)
    filename = f"invoice-{order.id}.pdf"
    msg.attach(filename, pdf_bytes, "application/pdf")

    msg.send()
