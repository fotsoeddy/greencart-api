from django.urls import path
from green_cart_api.promotion.api.views.promotion_views import (
    PromotionListCreateView,
    PromotionDetailView,
    ApplyPromotionView
)

app_name = 'promotion'

urlpatterns = [
    path('', PromotionListCreateView.as_view(), name='promotion-list-create'),
    path('<uuid:pk>/', PromotionDetailView.as_view(), name='promotion-detail'),
    path('apply/', ApplyPromotionView.as_view(), name='promotion-apply'),
]