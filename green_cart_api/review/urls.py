

# green_cart_api/review/urls.py

from django.urls import path
from green_cart_api.review.api.views.review_view import (
    ReviewListView, ReviewDetailView, ReviewMarkHelpfulView,
    ReviewApproveView, ReviewRejectView, ReviewImageListView,
    ReviewImageDetailView, ReviewHelpfulListView
)
app_name = 'review'
urlpatterns = [
    path('', ReviewListView.as_view(), name='review-list'), # Remarquez l'URL vide ici (si l'URL est /api/reviews)
    
    # 🚨 CORRECTION CLÉ : Remplacez <int:pk> par <uuid:pk> pour toutes les routes utilisant PK
    path('<uuid:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('<uuid:pk>/mark-helpful/', ReviewMarkHelpfulView.as_view(), name='review-mark-helpful'),
    path('<uuid:pk>/approve/', ReviewApproveView.as_view(), name='review-approve'),
    path('<uuid:pk>/reject/', ReviewRejectView.as_view(), name='review-reject'),
    
    path('review-images/', ReviewImageListView.as_view(), name='review-image-list'),
    path('review-images/<uuid:pk>/', ReviewImageDetailView.as_view(), name='review-image-detail'),
    path('review-helpful/', ReviewHelpfulListView.as_view(), name='review-helpful-list'),
]