# green_cart_api/cart/urls.py

from django.urls import path
from .api.views.cart_views import (
    MyCartView, AddItemView, RemoveItemView, UpdateQuantityView, ClearCartView
)

app_name = 'carts'

urlpatterns = [
    path('my-cart/', MyCartView.as_view(), name='my-cart'),
    path('<int:pk>/add-item/', AddItemView.as_view(), name='add-item'),
    path('<int:pk>/remove-item/', RemoveItemView.as_view(), name='remove-item'),
    path('<int:pk>/update-quantity/', UpdateQuantityView.as_view(), name='update-quantity'),
    path('<int:pk>/clear/', ClearCartView.as_view(), name='clear-cart'),
    # Si vous voulez un endpoint pour récupérer les détails du panier (GET /<pk>/), ajoutez :
    # path('<int:pk>/', CartDetailView.as_view({'get': 'get'}), name='cart-detail'),
]