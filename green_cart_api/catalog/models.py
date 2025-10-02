import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils.text import slugify
from green_cart_api.users.models import GreenCartBaseModel


class Category(GreenCartBaseModel):
    """
    Product category model for organizing products hierarchically.
    """
    name = models.CharField(
        max_length=255,
        help_text=_("Category name")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("URL-friendly version of the category name")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Detailed description of the category")
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        blank=True,
        null=True,
        help_text=_("Parent category for hierarchical structure")
    )
    image = models.ImageField(
        upload_to='category_images/',
        blank=True,
        null=True,
        help_text=_("Category image")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text=_("Order in which categories are displayed")
    )
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Whether this category is featured on the homepage")
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def has_children(self):
        return self.children.exists()


class Brand(GreenCartBaseModel):
    """
    Product brand model
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Brand name")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text=_("URL-friendly brand name")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Brand description")
    )
    logo = models.ImageField(
        upload_to='brand_logos/',
        blank=True,
        null=True,
        help_text=_("Brand logo")
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text=_("Brand website")
    )

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(GreenCartBaseModel):
    """
    Product tags for better search and categorization
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Tag name")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text=_("URL-friendly tag name")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Tag description")
    )

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(GreenCartBaseModel):
    """
    Main product model for the catalog.
    """
    # Basic Information
    name = models.CharField(
        max_length=255,
        help_text=_("Product name")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("URL-friendly version of the product name")
    )
    description = models.TextField(
        help_text=_("Detailed product description")
    )
    short_description = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_("Brief product description for listings")
    )
    
    # Categorization
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        help_text=_("Categories this product belongs to")
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text=_("Product brand")
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='products',
        blank=True,
        help_text=_("Product tags")
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Current selling price")
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Original price for showing discounts")
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Cost price for profit calculation")
    )
    
    quantity = models.PositiveIntegerField(
        default=0,
        help_text=_("Current stock quantity")
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text=_("Alert when stock reaches this level")
    )
    track_quantity = models.BooleanField(
        default=True,
        help_text=_("Whether to track inventory for this product")
    )
    allow_backorders = models.BooleanField(
        default=False,
        help_text=_("Allow orders when out of stock")
    )
    
    # Shipping
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Product weight in kilograms")
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Product dimensions (LxWxH)")
    )
    
    # SEO and Display
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("SEO meta title")
    )
    meta_description = models.TextField(
        blank=True,
        null=True,
        help_text=_("SEO meta description")
    )
    
    # Status Flags
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Featured product display")
    )
    is_bestseller = models.BooleanField(
        default=False,
        help_text=_("Mark as bestseller")
    )
    is_new = models.BooleanField(
        default=False,
        help_text=_("Mark as new product")
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['-created', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"GC{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_price exists"""
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount, 2)
        return 0

    @property
    def in_stock(self):
        """Check if product is in stock"""
        if not self.track_quantity:
            return True
        return self.quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        if not self.track_quantity:
            return False
        return self.quantity <= self.low_stock_threshold

    @property
    def primary_image(self):
        """Get the primary product image"""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()


class ProductImage(GreenCartBaseModel):
    """
    Product images model for storing multiple images per product.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        help_text=_("Product these images belong to")
    )
    image = models.ImageField(
        upload_to='product_images/',
        help_text=_("Product image")
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Alternative text for accessibility")
    )
    is_primary = models.BooleanField(
        default=False,
        help_text=_("Set as primary product image")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text=_("Order in which images are displayed")
    )

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ['is_primary', 'display_order', 'created']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)