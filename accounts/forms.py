# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Address


class CustomSignupForm(UserCreationForm):
    # We keep username + passwords for the user
    # Email is collected under the "Default shipping address" block
    full_name = forms.CharField(max_length=120, label="Full name")

    # Default shipping address (also used for contact)
    phone   = forms.CharField(max_length=20, label="Phone")
    email   = forms.EmailField(required=True, label="Email")  # stored on Address; copied to User.email
    line1   = forms.CharField(max_length=255, label="Address line 1")
    line2   = forms.CharField(max_length=255, required=False, label="Address line 2")
    city    = forms.CharField(max_length=120, label="City")
    state   = forms.CharField(max_length=120, label="State")
    pincode = forms.CharField(max_length=20, label="PIN code")
    country = forms.CharField(max_length=120, initial="India", label="Country")

    class Meta:
        model = User
        fields = [
            # account (left column)
            "username", "password1", "password2",
            # address (right column)
            "full_name", "phone", "email", "line1", "line2", "city", "state", "pincode", "country",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make everything look like Bootstrap controls
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()

    def save(self, commit=True):
        """
        Create the User, then create their default Address.

        We keep only one 'full_name' on the form; we split to first/last
        for convenience in places that use get_full_name().
        """
        user = super().save(commit=False)

        parts = self.cleaned_data.get("full_name", "").strip().split()
        user.first_name = parts[0] if parts else ""
        user.last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Copy address email onto the user so built-in flows (password reset, admin) keep working
        addr_email = self.cleaned_data["email"]
        user.email = addr_email

        if commit:
            user.save()
            Address.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                phone=self.cleaned_data["phone"],
                email=addr_email,  # stored on Address
                line1=self.cleaned_data["line1"],
                line2=self.cleaned_data.get("line2", ""),
                city=self.cleaned_data["city"],
                state=self.cleaned_data["state"],
                pincode=self.cleaned_data["pincode"],
                country=self.cleaned_data["country"],
                is_default=True,
            )
        return user


class UserForm(forms.ModelForm):
    """Used on profile edit page (left card)."""
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name":  forms.TextInput(attrs={"class": "form-control"}),
            "email":      forms.EmailInput(attrs={"class": "form-control"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model  = Address
        fields = ["full_name", "phone", "email", "line1", "line2", "city", "state", "pincode", "country", "is_default"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone":     forms.TextInput(attrs={"class": "form-control"}),
            "email":     forms.EmailInput(attrs={"class": "form-control"}),
            "line1":     forms.TextInput(attrs={"class": "form-control"}),
            "line2":     forms.TextInput(attrs={"class": "form-control"}),
            "city":      forms.TextInput(attrs={"class": "form-control"}),
            "state":     forms.TextInput(attrs={"class": "form-control"}),
            "pincode":   forms.TextInput(attrs={"class": "form-control"}),
            "country":   forms.TextInput(attrs={"class": "form-control"}),
        }


class PrettyPasswordChangeForm(PasswordChangeForm):
    """Give the auth password-change fields Bootstrap classes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-control"})
