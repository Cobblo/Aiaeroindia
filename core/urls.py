# core/urls.py
from django.urls import path
from . import views

app_name = "core"   # ← important for namespacing

urlpatterns = [
    path("", views.home, name="home"),
    path("soft/", views.soft, name="soft"),
    path("hard/", views.hard, name="hard"),
]
