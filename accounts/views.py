# accounts/views.py
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.urls import reverse

from .models import Address
from .forms import CustomSignupForm, UserForm, AddressForm


def signup(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import login
            login(request, user)
            return redirect("core:home")
    else:
        form = CustomSignupForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    """
    Combined profile page:
      - GET                -> view mode
      - GET ?edit=1        -> edit mode (user + default address)
      - POST (edit submit) -> save and return to view
    Shows the current default address (or first address if none default).
    """
    user = request.user

    # All addresses for display (optional in your template)
    addresses = Address.objects.filter(user=user).order_by("-is_default", "id")

    # choose the "primary" address for the edit form:
    address = (
        Address.objects.filter(user=user, is_default=True).first()
        or Address.objects.filter(user=user).first()
    )

    edit_mode = request.GET.get("edit") == "1"

    # If not editing, just show the profile page.
    if not edit_mode and request.method != "POST":
        return render(
            request,
            "accounts/profile.html",
            {
                "user_obj": user,
                "address": address,
                "addresses": addresses,
                "edit_mode": False,
            },
        )

    # From here on we are in edit mode (GET ?edit=1) OR handling POST save.
    if request.method == "POST":
        uform = UserForm(request.POST, instance=user)
        aform = AddressForm(request.POST, instance=address)
        if uform.is_valid() and aform.is_valid():
            uform.save()

            addr = aform.save(commit=False)
            addr.user = user
            # Save the address being edited/created as the default if none exists
            addr.save()

            # Ensure exactly one default if requested or if none exists
            want_default = bool(request.POST.get("is_default"))
            has_default = Address.objects.filter(user=user, is_default=True).exclude(pk=addr.pk).exists()

            if want_default or not has_default:
                # Set this one default and unset others
                Address.objects.filter(user=user).exclude(pk=addr.pk).update(is_default=False)
                if not addr.is_default:
                    addr.is_default = True
                    addr.save(update_fields=["is_default"])

            messages.success(request, "Profile updated.")
            # Go back to view mode
            return redirect("accounts:profile")
        else:
            # stay in edit mode, show errors
            return render(
                request,
                "accounts/profile.html",
                {
                    "user_obj": user,
                    "address": address,
                    "addresses": addresses,
                    "edit_mode": True,
                    "uform": uform,
                    "aform": aform,
                },
            )

    # GET with ?edit=1 — build forms and show edit UI
    uform = UserForm(instance=user)
    aform = AddressForm(instance=address)
    return render(
        request,
        "accounts/profile.html",
        {
            "user_obj": user,
            "address": address,
            "addresses": addresses,
            "edit_mode": True,
            "uform": uform,
            "aform": aform,
        },
    )


# ---------------------------
# Address helpers & endpoints
# ---------------------------

def _normalize_address_post(data, prefix=""):
    """
    Extract address fields from POST. Supports:
      - plain fields: full_name, line1, line2, city, state, pincode, country, phone, is_default
      - or prefixed fields (e.g. 'edit_full_name' when prefix='edit_')
    Returns a dict suitable for AddressForm or manual assignment.
    """
    def g(key, default=""):
        return data.get(f"{prefix}{key}", default)

    out = {
        "full_name": g("full_name"),
        "line1": g("line1"),
        "line2": g("line2"),
        "city": g("city"),
        "state": g("state"),
        "pincode": g("pincode"),
        "country": g("country") or "India",
        "phone": g("phone"),
        # For checkboxes: present => True; absent => False
        "is_default": bool(data.get(f"{prefix}is_default")),
    }
    return out


@login_required
def address_create(request):
    """
    Create a new address (used by the 'Add New Address' checkout modal).
    Accepts plain field names (no prefix).
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    payload = _normalize_address_post(request.POST, prefix="")  # no prefix for add modal

    form = AddressForm(payload)
    if form.is_valid():
        addr = form.save(commit=False)
        addr.user = request.user
        addr.save()

        # Default handling: if requested or if user has no default yet
        if payload["is_default"] or not Address.objects.filter(user=request.user, is_default=True).exclude(pk=addr.pk).exists():
            Address.objects.filter(user=request.user).exclude(pk=addr.pk).update(is_default=False)
            if not addr.is_default:
                addr.is_default = True
                addr.save(update_fields=["is_default"])

        messages.success(request, "Address added.")
    else:
        messages.error(request, "Please correct the errors in the address form.")

    # Return to checkout by default; support ?next=…
    return redirect(request.GET.get("next") or request.POST.get("next") or "orders:checkout")


@login_required
def address_update(request):
    """
    Update an address (used by the 'Edit Address' checkout modal).
    Accepts both:
      - edit_*-prefixed fields (from the modal include),
      - or plain field names.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    addr_id = request.POST.get("id") or request.POST.get("edit_id")
    addr = get_object_or_404(Address, pk=addr_id, user=request.user)

    # Try prefixed first (checkout modal), then fallback to plain
    payload = _normalize_address_post(request.POST, prefix="edit_")
    if not payload["full_name"] and not payload["line1"]:
        payload = _normalize_address_post(request.POST, prefix="")

    form = AddressForm(payload, instance=addr)
    if form.is_valid():
        addr = form.save()

        # Default handling
        if payload["is_default"]:
            Address.objects.filter(user=request.user).exclude(pk=addr.pk).update(is_default=False)
            if not addr.is_default:
                addr.is_default = True
                addr.save(update_fields=["is_default"])
        else:
            # If user has no other default, keep this one as default
            if not Address.objects.filter(user=request.user, is_default=True).exists():
                addr.is_default = True
                addr.save(update_fields=["is_default"])

        messages.success(request, "Address updated.")
    else:
        messages.error(request, "Please correct the errors in the address form.")

    return redirect(request.GET.get("next") or request.POST.get("next") or "orders:checkout")


# ---------- Optional convenience endpoints ----------

@login_required
def address_delete(request, pk):
    """
    Delete an address owned by the user. If it was default, make another one default if any.
    """
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    was_default = addr.is_default
    addr.delete()

    if was_default:
        other = Address.objects.filter(user=request.user).first()
        if other and not other.is_default:
            other.is_default = True
            other.save(update_fields=["is_default"])

    messages.success(request, "Address removed.")
    return redirect(request.GET.get("next") or "accounts:profile")


@login_required
def address_set_default(request, pk):
    """
    Explicitly set one address as default, unsetting the others.
    """
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).exclude(pk=addr.pk).update(is_default=False)
    if not addr.is_default:
        addr.is_default = True
        addr.save(update_fields=["is_default"])
    messages.success(request, "Default address updated.")
    return redirect(request.GET.get("next") or "accounts:profile")
