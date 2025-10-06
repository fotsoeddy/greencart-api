from django.urls import path
from .api.views import (
    WishlistRetrieveView,
    WishlistSettingsUpdateView,
    WishlistItemCreateView,
    WishlistItemDeleteView,
    WishlistClearView,
    WishlistMoveToCartView,
    PublicWishlistView,
)

app_name = 'wishlist'

urlpatterns = [
    path('', WishlistRetrieveView.as_view(), name='wishlist-detail'),
    path('settings/', WishlistSettingsUpdateView.as_view(), name='wishlist-settings'),
    path('items/', WishlistItemCreateView.as_view(), name='wishlist-item-create'),
    path('items/<uuid:item_id>/', WishlistItemDeleteView.as_view(), name='wishlist-item-delete'),
    path('items/<uuid:item_id>/move-to-cart/', WishlistMoveToCartView.as_view(), name='wishlist-item-move-to-cart'),
    path('clear/', WishlistClearView.as_view(), name='wishlist-clear'),
    path('public/<int:user_id>/', PublicWishlistView.as_view(), name='wishlist-public-view'),
]


