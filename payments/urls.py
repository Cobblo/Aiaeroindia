from django.urls import path
from .views import pay, verify

app_name = "payments"

urlpatterns = [
    path("pay/", pay, name="pay"),
    path("verify/", verify, name="verify"),
]
