from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from pathlib import Path


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    # SKU: keep unique, auto-generate if left blank
    sku = models.CharField(
        max_length=64, unique=True, blank=True,
        help_text="Leave empty to auto-generate (e.g. CAT-000123)."
    )

    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # ---------- helpers ----------
    def _gen_sku_base(self) -> str:
        base = (self.category.name if self.category else self.name or "SKU")
        base = "".join(ch for ch in base.upper() if ch.isalnum())
        return (base[:3] or "SKU")

    def _ensure_slug(self):
        if not self.slug:
            self.slug = slugify(self.name)

    def _ensure_sku(self):
        if not self.sku and self.pk:
            self.sku = f"{self._gen_sku_base()}-{self.pk:06d}"

    # ---------- save ----------
    def save(self, *args, **kwargs):
        creating = self.pk is None
        self._ensure_slug()
        result = super().save(*args, **kwargs)
        if creating and not self.sku:
            self._ensure_sku()
            super(Product, self).save(update_fields=["sku"])
        return result

    # ---------- misc ----------
    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])

    def __str__(self):
        return f"{self.name} [{self.sku}]" if self.sku else self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt = models.CharField(max_length=140, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductAttachment(models.Model):
    product = models.ForeignKey(
        "catalog.Product",
        related_name="attachments",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to="product_files/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or Path(self.file.name).name

    @property
    def filename(self):
        return Path(self.file.name).name

    @property
    def ext(self):
        return Path(self.file.name).suffix.lower().lstrip(".")
