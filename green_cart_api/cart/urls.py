# green_cart_api/cart/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views.cart_views import CartViewSet

app_name = 'carts'  # Changez en pluriel pour cohérence

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')  # Enregistre le ViewSet sans préfixe supplémentaire

urlpatterns = [
    path('', include(router.urls)),  # Inclut les URL auto-générées : / (list/create), /<pk>/ (detail/update/delete)
    
    # Actions personnalisées (si non gérées par le router, ajoutez-les manuellement)
    path('my-cart/', CartViewSet.as_view({'get': 'get_my_cart'}), name='my-cart'),
    path('<int:pk>/add-item/', CartViewSet.as_view({'post': 'add_item'}), name='add-item'),
    path('<int:pk>/remove-item/', CartViewSet.as_view({'post': 'remove_item'}), name='remove-item'),
    path('<int:pk>/update-quantity/', CartViewSet.as_view({'post': 'update_quantity'}), name='update-quantity'),
    path('<int:pk>/clear/', CartViewSet.as_view({'post': 'clear_cart'}), name='clear-cart'),
]