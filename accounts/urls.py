# accounts/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView

from . import views  # <-- import the module so we can reference all view funcs
from .forms import PrettyPasswordChangeForm

app_name = "accounts"

urlpatterns = [
    # Profile & signup
    path("profile/", views.profile, name="profile"),
    path("signup/", views.signup, name="signup"),

    # Address management (used by checkout modals)
    path("address/create/", views.address_create, name="address_create"),
    path("address/update/", views.address_update, name="address_update"),
    # Optional convenience routes (only if you added these views)
    path("address/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("address/<int:pk>/default/", views.address_set_default, name="address_set_default"),

    # Password change
    path(
        "password_change/",
        PasswordChangeView.as_view(
            form_class=PrettyPasswordChangeForm,
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
