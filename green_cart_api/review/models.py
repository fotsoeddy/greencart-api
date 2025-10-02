import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from green_cart_api.users.models import GreenCartBaseModel
from green_cart_api.global_data.enm import ReviewStatus


class Review(GreenCartBaseModel):
    """
    Product reviews and ratings by customers
    """
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text=_("Product being reviewed")
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text=_("User who wrote the review")
    )
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='reviews',
        blank=True,
        null=True,
        help_text=_("Order associated with this review")
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Rating from 1 to 5 stars")
    )
    title = models.CharField(
        max_length=255,
        help_text=_("Review title")
    )
    comment = models.TextField(
        help_text=_("Detailed review comment")
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        help_text=_("Review status")
    )
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text=_("Whether the reviewer purchased the product")
    )
    helpful_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of users who found this review helpful")
    )

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        unique_together = ['product', 'user']
        ordering = ['-created']

    def __str__(self):
        return f"Review for {self.product.name} by {self.user}"

    def save(self, *args, **kwargs):
        # Auto-verify purchase if order exists
        if self.order and not self.is_verified_purchase:
            self.is_verified_purchase = True
        super().save(*args, **kwargs)

    def mark_helpful(self):
        """Increment helpful count"""
        self.helpful_count += 1
        self.save()

    def approve(self):
        """Approve the review"""
        self.status = ReviewStatus.APPROVED
        self.save()

    def reject(self):
        """Reject the review"""
        self.status = ReviewStatus.REJECTED
        self.save()


class ReviewImage(GreenCartBaseModel):
    """
    Images attached to reviews
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images',
        help_text=_("Parent review")
    )
    image = models.ImageField(
        upload_to='review_images/',
        help_text=_("Review image")
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Alternative text for accessibility")
    )

    class Meta:
        verbose_name = _("Review Image")
        verbose_name_plural = _("Review Images")

    def __str__(self):
        return f"Image for review by {self.review.user}"


class ReviewHelpful(GreenCartBaseModel):
    """
    Track which users found which reviews helpful
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        help_text=_("Review marked as helpful")
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        help_text=_("User who found the review helpful")
    )

    class Meta:
        verbose_name = _("Review Helpful")
        verbose_name_plural = _("Review Helpful Votes")
        unique_together = ['review', 'user']

    def __str__(self):
        return f"{self.user} found review by {self.review.user} helpful"