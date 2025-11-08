from django.views.generic import ListView
from .models import Customer

class CustomerListView(ListView):
    template_name = "customers/list.html"
    model = Customer
    context_object_name = "customers"
