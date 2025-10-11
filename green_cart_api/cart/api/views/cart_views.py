from rest_framework.views import APIView  # Base pour vues custom
from rest_framework.generics import GenericAPIView  # Pour retrieve/update si besoin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from green_cart_api.cart.models import Cart, CartItem
from green_cart_api.cart.api.serializers.cart_serializers import CartSerializer, CartItemSerializer
from green_cart_api.catalog.models import Product
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

class MyCartView(APIView):
    """
    Vue pour récupérer ou créer le panier actuel de l'utilisateur/session.
    Méthode: GET
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Get current cart",
        description="Retrieve or create the current user's cart. For authenticated users, returns their cart. For anonymous users, creates a session-based cart.",
        responses={
            200: OpenApiResponse(
                response=CartSerializer,
                description="Current cart",
                examples=[
                    OpenApiExample(
                        "Cart with items",
                        summary="Cart containing products",
                        description="Response showing cart with multiple items",
                        value={
                            "id": 1,
                            "user": 1,
                            "session_key": None,
                            "is_active": True,
                            "items": [
                                {
                                    "id": 1,
                                    "product": {
                                        "id": 1,
                                        "name": "iPhone 15",
                                        "slug": "iphone-15",
                                        "price": "999.00",
                                        "compare_price": "1099.00",
                                        "discount_percentage": "9.10",
                                        "in_stock": True,
                                        "is_featured": True,
                                        "is_bestseller": True,
                                        "is_new": False,
                                        "brand": "apple",
                                        "categories": ["phones"],
                                        "tags": ["ios"],
                                        "created": "2025-01-01T12:00:00Z"
                                    },
                                    "quantity": 2,
                                    "unit_price": "999.00",
                                    "total_price": "1998.00",
                                    "created": "2025-01-02T12:00:00Z"
                                },
                                {
                                    "id": 2,
                                    "product": {
                                        "id": 2,
                                        "name": "MacBook Pro",
                                        "slug": "macbook-pro",
                                        "price": "1999.00",
                                        "compare_price": None,
                                        "discount_percentage": 0,
                                        "in_stock": True,
                                        "is_featured": True,
                                        "is_bestseller": False,
                                        "is_new": True,
                                        "brand": "apple",
                                        "categories": ["laptops"],
                                        "tags": ["macos"],
                                        "created": "2025-01-01T12:00:00Z"
                                    },
                                    "quantity": 1,
                                    "unit_price": "1999.00",
                                    "total_price": "1999.00",
                                    "created": "2025-01-02T12:00:00Z"
                                }
                            ],
                            "total_items": 3,
                            "subtotal": "3997.00",
                            "created": "2025-01-01T12:00:00Z",
                            "modified": "2025-01-02T12:00:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Error retrieving cart")
        }
    )
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
    @extend_schema(
        summary="Add item to cart",
        description="Add a product to the cart with specified quantity.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'integer', 'description': 'Product ID to add'},
                    'quantity': {'type': 'integer', 'default': 1, 'description': 'Quantity to add'}
                },
                'required': ['product_id']
            }
        },
        responses={
            201: OpenApiResponse(
                response=CartItemSerializer,
                description="Item added to cart",
                examples=[
                    OpenApiExample(
                        "Add item request",
                        summary="Add product to cart",
                        description="Request body for adding item to cart",
                        value={
                            "product_id": 1,
                            "quantity": 2
                        },
                        request_only=True,
                    ),
                    OpenApiExample(
                        "Item added response",
                        summary="Successfully added item",
                        description="Response after successful item addition",
                        value={
                            "id": 1,
                            "product": {
                                "id": 1,
                                "name": "iPhone 15",
                                "slug": "iphone-15",
                                "price": "999.00",
                                "compare_price": "1099.00",
                                "discount_percentage": "9.10",
                                "in_stock": True,
                                "is_featured": True,
                                "is_bestseller": True,
                                "is_new": False,
                                "brand": "apple",
                                "categories": ["phones"],
                                "tags": ["ios"],
                                "created": "2025-01-01T12:00:00Z"
                            },
                            "quantity": 2,
                            "unit_price": "999.00",
                            "total_price": "1998.00",
                            "created": "2025-01-02T12:00:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input or error adding item"),
            404: OpenApiResponse(description="Product not found")
        }
    )
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
    @extend_schema(
        summary="Remove item from cart",
        description="Remove a product from the cart.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'integer', 'description': 'Product ID to remove'}
                },
                'required': ['product_id']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Item removed successfully",
                examples=[
                    OpenApiExample(
                        "Remove item request",
                        summary="Remove product from cart",
                        description="Request body for removing item from cart",
                        value={
                            "product_id": 1
                        },
                        request_only=True,
                    ),
                    OpenApiExample(
                        "Item removed response",
                        summary="Successfully removed item",
                        description="Response after successful item removal",
                        value={
                            "message": "Item removed successfully"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Error removing item"),
            404: OpenApiResponse(description="Product not found")
        }
    )
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
    @extend_schema(
        summary="Update item quantity",
        description="Update the quantity of a product in the cart.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'integer', 'description': 'Product ID to update'},
                    'quantity': {'type': 'integer', 'description': 'New quantity'}
                },
                'required': ['product_id', 'quantity']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Quantity updated successfully",
                examples=[
                    OpenApiExample(
                        "Update quantity request",
                        summary="Update product quantity",
                        description="Request body for updating item quantity",
                        value={
                            "product_id": 1,
                            "quantity": 3
                        },
                        request_only=True,
                    ),
                    OpenApiExample(
                        "Quantity updated response",
                        summary="Successfully updated quantity",
                        description="Response after successful quantity update",
                        value={
                            "message": "Quantity updated successfully"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input or error updating quantity"),
            404: OpenApiResponse(description="Product not found")
        }
    )
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
    @extend_schema(
        summary="Clear cart",
        description="Remove all items from the cart.",
        responses={
            200: OpenApiResponse(
                description="Cart cleared successfully",
                examples=[
                    OpenApiExample(
                        "Cart cleared response",
                        summary="Successfully cleared cart",
                        description="Response after successful cart clearing",
                        value={
                            "message": "Cart cleared successfully"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(description="Error clearing cart")
        }
    )
    def post(self, request, pk=None):
        cart = self.get_object()
        cart.clear()
        return Response({'message': _("Cart cleared successfully")}, status=status.HTTP_200_OK)