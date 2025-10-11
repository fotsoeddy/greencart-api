from rest_framework.views import APIView  # Base pour vues custom
from rest_framework.generics import GenericAPIView  # Pour retrieve/update si besoin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from green_cart_api.cart.models import Cart, CartItem
from green_cart_api.cart.api.serializers.cart_serializers import CartSerializer, CartItemSerializer
from green_cart_api.catalog.models import Product

class MyCartView(APIView):
    """
    Vue pour récupérer ou créer le panier actuel de l'utilisateur/session.
    Méthode: GET
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        try:
            cart = self.get_cart(request)
            if not cart:
                cart = self.create_cart(request)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_cart(self, request):
        if request.user.is_authenticated:
            return Cart.objects.filter(user=request.user, is_active=True).first()
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            return Cart.objects.filter(session_key=session_key, is_active=True).first()

    def create_cart(self, request):
        if request.user.is_authenticated:
            return Cart.objects.create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
            return Cart.objects.create(session_key=request.session.session_key)

class CartDetailView(GenericAPIView):
    """
    Vue de base pour les actions sur un panier spécifique (via pk).
    Utilisée comme mixin pour les autres vues.
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user, is_active=True)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            return Cart.objects.filter(session_key=session_key, is_active=True)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.filter(pk=self.kwargs['pk']).first()
        if not obj:
            raise Cart.DoesNotExist
        self.check_object_permissions(self.request, obj)
        return obj

class AddItemView(CartDetailView):
    """
    Vue pour ajouter un item au panier.
    Méthode: POST, avec 'product_id' et 'quantity' (optionnel) dans le body.
    """
    def post(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            product = Product.objects.get(id=product_id)
            cart_item = cart.add_item(product, quantity)
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RemoveItemView(CartDetailView):
    """
    Vue pour supprimer un item du panier.
    Méthode: POST, avec 'product_id' dans le body.
    """
    def post(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            cart.remove_item(product)
            return Response({'message': _("Item removed successfully")}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UpdateQuantityView(CartDetailView):
    """
    Vue pour updater la quantité d'un item.
    Méthode: POST, avec 'product_id' et 'quantity' dans le body.
    """
    def post(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            product = Product.objects.get(id=product_id)
            cart.update_item_quantity(product, quantity)
            return Response({'message': _("Quantity updated successfully")}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': _("Product not found")}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ClearCartView(CartDetailView):
    """
    Vue pour vider le panier.
    Méthode: POST.
    """
    def post(self, request, pk=None):
        cart = self.get_object()
        cart.clear()
        return Response({'message': _("Cart cleared successfully")}, status=status.HTTP_200_OK)