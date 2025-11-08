# cart/cart.py
from __future__ import annotations

from django.conf import settings

SESSION_KEY = getattr(settings, "CART_SESSION_KEY", "cart")

class Cart:
    """
    Session-backed cart.
    Session structure:
        request.session['cart'] = {
            "<product_id_as_str>": {"qty": int},
            ...
        }
    No magic keys like "__count" or "__total".
    """

    SESSION_KEY = getattr(settings, "CART_SESSION_KEY", "cart")

    def __init__(self, request):
        self.request = request
        self.session = request.session
        # Ensure dict exists
        cart = self.session.get(self.SESSION_KEY)
        if not isinstance(cart, dict):
            cart = {}
            self.session[self.SESSION_KEY] = cart
            self.session.modified = True
        # Remove any legacy/magic keys that start with "__"
        self._sanitize()

    # ---------- internal helpers ----------

    def _get_store(self) -> dict:
        store = self.session.get(self.SESSION_KEY, {})
        if not isinstance(store, dict):
            store = {}
            self.session[self.SESSION_KEY] = store
        return store

    def _save_store(self, store: dict) -> None:
        self.session[self.SESSION_KEY] = store
        self.session.modified = True

    def _sanitize(self) -> None:
        store = self._get_store()
        changed = False
        for k in list(store.keys()):
            if isinstance(k, str) and k.startswith("__"):
                store.pop(k, None)
                changed = True
        if changed:
            self._save_store(store)

    # ---------- public API ----------

    def add(self, product_id: int | str, qty: int = 1, update: bool = False) -> None:
        store = self._get_store()
        pid = str(product_id)

        if pid not in store or not isinstance(store[pid], dict):
            store[pid] = {"qty": 0}

        current = int(store[pid].get("qty", 0))
        if update:
            store[pid]["qty"] = max(1, int(qty))
        else:
            store[pid]["qty"] = max(1, current + int(qty))

        self._save_store(store)

    def remove(self, product_id: int | str) -> None:
        store = self._get_store()
        pid = str(product_id)
        if pid in store:
            del store[pid]
            self._save_store(store)

    def clear(self) -> None:
        self._save_store({})

    @property
    def count(self) -> int:
        """Total quantity of items."""
        store = self._get_store()
        total = 0
        for v in store.values():
            if isinstance(v, dict):
                try:
                    total += int(v.get("qty", 0))
                except Exception:
                    continue
        return total

    def __len__(self) -> int:
        """Number of distinct lines."""
        store = self._get_store()
        return sum(1 for v in store.values() if isinstance(v, dict))

    def __iter__(self):
        """
        Yields dicts:
          {
            'product': Product,
            'product_id': int,
            'qty': int,
            'price': Decimal,
            'subtotal': Decimal,
          }
        """
        from catalog.models import Product  # local import to avoid circulars

        store = self._get_store()
        product_ids = [int(k) for k in store.keys() if isinstance(k, str) and k.isdigit()]
        if not product_ids:
            return
        products = Product.objects.filter(id__in=product_ids)
        prod_map = {p.id: p for p in products}

        for pid_str, data in store.items():
            if not isinstance(pid_str, str) or not pid_str.isdigit():
                continue
            if not isinstance(data, dict):
                continue

            pid = int(pid_str)
            product = prod_map.get(pid)
            if not product:
                # silently skip products that no longer exist
                continue

            try:
                qty = max(1, int(data.get("qty", 0)))
            except Exception:
                qty = 1

            price = product.price
            subtotal = price * qty

            yield {
                "product": product,
                "product_id": pid,
                "qty": qty,
                "price": price,
                "subtotal": subtotal,
            }

    @property
    def total(self):
        """Cart total computed from line subtotals."""
        total = 0
        for item in self:
            total += item["subtotal"]
        return total
