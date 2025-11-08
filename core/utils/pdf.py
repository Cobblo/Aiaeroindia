# core/utils/pdf.py
import os
import base64
from io import BytesIO
from django.template.loader import render_to_string, get_template
from django.conf import settings


def render_pdf_from_template(template_name: str, context: dict) -> bytes:
    """
    Generate PDF bytes from a Django template.
    Order of engines: WeasyPrint -> xhtml2pdf -> ReportLab (fallback).
    Writes a debug copy when DEBUG=True.
    """
    # Log the resolved template path (useful during setup)
    try:
        t = get_template(template_name)
        origin = getattr(t, "origin", None)
        print(f"[PDF] Using template '{template_name}' -> {getattr(origin, 'name', 'unknown')}")
    except Exception:
        pass

    html = render_to_string(template_name, context)

    # 1) WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore
        pdf_io = BytesIO()
        HTML(string=html).write_pdf(pdf_io)
        data = pdf_io.getvalue()
        if data:
            _debug_save_pdf(data, "weasyprint")
            print("[PDF] Generated with WeasyPrint.")
            return data
    except Exception as e:
        print(f"[WARN] WeasyPrint failed: {e}")

    # 2) xhtml2pdf
    try:
        from xhtml2pdf import pisa  # type: ignore
        pdf_io = BytesIO()
        result = pisa.CreatePDF(html, dest=pdf_io, encoding="UTF-8")
        if result.err:
            raise RuntimeError("xhtml2pdf reported an error")
        data = pdf_io.getvalue()
        if not data:
            raise RuntimeError("xhtml2pdf returned empty PDF")
        _debug_save_pdf(data, "xhtml2pdf")
        print("[PDF] Generated with xhtml2pdf.")
        return data
    except Exception as e:
        print(f"[WARN] xhtml2pdf failed: {e}")

    # 3) ReportLab fallback (no HTML)
    try:
        data = _render_reportlab_invoice(context)
        _debug_save_pdf(data, "reportlab")
        print("[PDF] Generated with ReportLab fallback.")
        return data
    except Exception as e:
        raise RuntimeError(f"ReportLab fallback failed: {e}") from e


def _debug_save_pdf(data: bytes, engine: str):
    """Save the produced PDF to project root in DEBUG mode."""
    if not getattr(settings, "DEBUG", False):
        return
    try:
        base_dir = getattr(settings, "BASE_DIR", os.getcwd())
        path = os.path.join(base_dir, f"__last_invoice_{engine}.pdf")
        with open(path, "wb") as f:
            f.write(data)
        print(f"[DEBUG] Wrote PDF to {path} ({len(data)} bytes)")
    except Exception as e:
        print(f"[WARN] Could not write debug PDF: {e}")


# ----------------------- ReportLab fallback -----------------------

def _render_reportlab_invoice(ctx: dict) -> bytes:
    """
    Build a neat invoice using ReportLab (no HTML).
    Expects in ctx:
      - order
      - line_items: list of dicts {'name','qty','price','line_total'} (all STRINGS)
      - subtotal_str / tax_str / shipping_str / total_str (strings)  OR
        subtotal / tax / shipping / total (Decimals)
      - tax_rate_pct (string, optional)
      - company_logo_b64 (base64 PNG, optional)
      - company_name / company_email (strings)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.colors import Color

    def _pick_money(key_str, key_dec):
        """Prefer 'xyz_str', else format Decimal at 'xyz' if present, else '0.00'."""
        if ctx.get(key_str) is not None:
            return str(ctx.get(key_str))
        val = ctx.get(key_dec)
        try:
            return f"{float(val):.2f}"
        except Exception:
            return "0.00"

    order = ctx.get("order")
    line_items = ctx.get("line_items", [])
    company_name = ctx.get("company_name", "Company")
    company_email = ctx.get("company_email", "")
    company_logo_b64 = ctx.get("company_logo_b64")
    tax_rate_pct = str(ctx.get("tax_rate_pct", ""))  # purely display

    # Totals (accept *_str or Decimal)
    subtotal_str = _pick_money("subtotal_str", "subtotal")
    shipping_str = _pick_money("shipping_str", "shipping")
    tax_str      = _pick_money("tax_str", "tax")
    total_str    = _pick_money("total_str", "total")
    if (not total_str or total_str == "0.00") and ctx.get("order_total_str"):
        total_str = str(ctx["order_total_str"])

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x_margin = 20 * mm
    gutter = 8 * mm
    y = height - 25 * mm

    # ---- Header: logo + title ----
    if company_logo_b64:
        try:
            img = ImageReader(BytesIO(base64.b64decode(company_logo_b64)))
            c.drawImage(
                img, x_margin, y - 12 * mm,
                width=32 * mm, height=12 * mm,
                preserveAspectRatio=True, mask='auto'
            )
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - x_margin, y, "Invoice")

    c.setFont("Helvetica", 9)
    c.drawRightString(width - x_margin, y - 6 * mm, f"Order #{getattr(order, 'id', '')}")
    created_at = getattr(order, "created_at", None)
    if created_at:
        c.drawRightString(
            width - x_margin,
            y - 10 * mm,
            f"Placed on {created_at.strftime('%b %d, %Y, %I:%M %p')}",
        )
    y -= 18 * mm

    # ---- Company block ----
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_margin, y, company_name or "")
    c.setFont("Helvetica", 9)
    c.drawString(x_margin, y - 5 * mm, company_email or "")
    y -= 12 * mm

    # -------- Addresses --------
    box_w   = (width - 2 * x_margin - gutter) / 2.0
    line_h  = 12.0
    padding = 4 * mm

    bill_lines, ship_lines = _build_address_lines(order)

    left_used = _draw_box_with_title_and_lines(
        c, title="Bill To", x=x_margin, y=y,
        box_w=box_w, line_h=line_h, lines=bill_lines, padding=padding
    )
    right_used = _draw_box_with_title_and_lines(
        c, title="Ship To", x=x_margin + box_w + gutter, y=y,
        box_w=box_w, line_h=line_h, lines=ship_lines, padding=padding
    )
    y -= max(left_used, right_used) + 8 * mm

    # -------- Items header --------
    c.setFont("Helvetica-Bold", 9)
    col1 = x_margin
    col2 = width - (65 * mm)
    col3 = width - (40 * mm)
    col4 = width - x_margin
    c.drawString(col1, y, "Product")
    c.drawRightString(col2, y, "Qty")
    c.drawRightString(col3, y, "Price")
    c.drawRightString(col4, y, "Line Total")
    y -= 4 * mm
    c.setStrokeColor(Color(0, 0, 0, alpha=0.4))
    c.line(x_margin, y, width - x_margin, y)
    y -= 5 * mm

    # -------- Items rows --------
    c.setFont("Helvetica", 9)
    item_line_h = 12.0
    for li in line_items:
        name  = (li.get("name") or "")[:200]
        qty   = li.get("qty") or "0"
        price = li.get("price") or "0.00"
        total = li.get("line_total") or "0.00"

        max_name_w = col2 - col1 - 4
        name_lines = _wrap_text(c, name, "Helvetica", 9, max_name_w)

        for idx, nl in enumerate(name_lines):
            c.drawString(col1, y, nl)
            if idx == 0:
                c.drawRightString(col2, y, qty)
                c.drawRightString(col3, y, f"Rs. {price}")
                c.drawRightString(col4, y, f"Rs. {total}")
            y -= item_line_h
            if y < 30 * mm:
                c.showPage()
                y = height - 25 * mm
                c.setFont("Helvetica", 9)

        c.setStrokeColor(Color(0, 0, 0, alpha=0.12))
        c.line(x_margin, y + 2, width - x_margin, y + 2)
        y -= 2

    # -------- Totals (Subtotal, Shipping, Tax, Total) --------
    y -= 4 * mm
    c.setStrokeColor(Color(0, 0, 0, alpha=0.4))
    c.line(x_margin, y, width - x_margin, y)
    y -= 8 * mm

    def _row(label, value, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10 if bold else 9)
        c.drawRightString(col3, y, label)
        c.drawRightString(col4, y, f"Rs. {value}")
        y -= 6 * mm

    _row("Subtotal", subtotal_str)
    _row("Shipping", "0.00" if shipping_str in ("", "0", "0.00") else shipping_str)
    _row(f"Tax{f' ({tax_rate_pct}%)' if tax_rate_pct else ''}", tax_str)
    _row("Grand Total", total_str, bold=True)

    c.showPage()
    c.save()
    return buf.getvalue()


def _build_address_lines(order):
    """Return (bill_lines, ship_lines) lists of strings; always safe."""
    bill_lines, ship_lines = [], []
    addr = getattr(order, "address", None)
    if addr:
        bill_lines.append(getattr(addr, "full_name", "") or "")
        bill_lines.append((
            (getattr(addr, "line1", "") or "") +
            (", " + getattr(addr, "line2")) if getattr(addr, "line2", "") else ""
        ).strip(", "))
        bill_lines.append(" ".join([s for s in [
            getattr(addr, "city", "") or "",
            getattr(addr, "state", "") or "",
            getattr(addr, "zip", "") or "",
        ] if s]).strip())
        bill_lines.append(getattr(addr, "country", "") or "")
        bill_lines.append(getattr(order, "email", None) or getattr(addr, "email", "") or "")
        ship_lines = bill_lines[:]  # same for this layout
    else:
        bill_lines.append(getattr(order, "billing_name", "") or "")
        bill_lines.append(getattr(order, "billing_address", "") or "")
        bill_lines.append(" ".join([s for s in [
            getattr(order, "billing_city", "") or "",
            getattr(order, "billing_state", "") or "",
            getattr(order, "billing_zip", "") or "",
        ] if s]).strip())
        bill_lines.append(getattr(order, "billing_country", "") or "")
        bill_lines.append(getattr(order, "email", "") or "")

        ship_lines.append(getattr(order, "shipping_name", "") or "")
        ship_lines.append(getattr(order, "shipping_address", "") or "")
        ship_lines.append(" ".join([s for s in [
            getattr(order, "shipping_city", "") or "",
            getattr(order, "shipping_state", "") or "",
            getattr(order, "shipping_zip", "") or "",
        ] if s]).strip())
        ship_lines.append(getattr(order, "shipping_country", "") or "")
    return bill_lines, ship_lines


def _wrap_text(c, text, font_name, font_size, max_width):
    """Simple word-wrap using stringWidth. Returns list of lines that fit max_width."""
    c.setFont(font_name, font_size)
    words = (text or "").split()
    if not words:
        return [""]

    lines, cur = [], words[0]
    for w in words[1:]:
        trial = cur + " " + w
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _draw_box_with_title_and_lines(c, title, x, y, box_w, line_h, lines, padding=6):
    """Draw a light bordered box with a title and wrapped content. Return used height."""
    from reportlab.lib.colors import Color

    wrapped_lines = []
    max_text_w = box_w - 2 * padding
    for line in (lines or []):
        wrapped_lines.extend(_wrap_text(c, line or "", "Helvetica", 9, max_text_w))

    title_h   = 12.0
    content_h = len(wrapped_lines) * line_h
    box_h     = padding + title_h + 4 + content_h + padding

    c.setStrokeColor(Color(0, 0, 0, alpha=0.15))
    c.rect(x, y - box_h, box_w, box_h, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + padding, y - padding - 2, title)

    c.setFont("Helvetica", 9)
    cursor_y = y - padding - title_h - 6
    for wl in wrapped_lines:
        c.drawString(x + padding, cursor_y, wl)
        cursor_y -= line_h

    return box_h
