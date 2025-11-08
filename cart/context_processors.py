from django.db.models import Sum
from .models import CartItem

def cart_summary(request):
    if request.user.is_authenticated:
        count = (CartItem.objects
                 .filter(user=request.user)
                 .aggregate(n=Sum("quantity"))["n"] or 0)
    else:
        sk = request.session.session_key
        if not sk:
            request.session.create()
            sk = request.session.session_key
        count = (CartItem.objects
                 .filter(session_key=sk)
                 .aggregate(n=Sum("quantity"))["n"] or 0)
    return {"cart_count": count}
