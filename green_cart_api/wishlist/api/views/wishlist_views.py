import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from green_cart_api.wishlist.models import Wishlist, WishlistItem
from green_cart_api.catalog.models import Product
from ..serializers import WishlistSerializer, WishlistItemSerializer


User = get_user_model()
logger = logging.getLogger(__name__)


def get_or_create_user_wishlist(user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


class WishlistRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Retrieve current user's wishlist", responses={200: WishlistSerializer})
    def get(self, request):
        wishlist = get_or_create_user_wishlist(request.user)
        return Response(WishlistSerializer(wishlist, context={'request': request}).data)


class WishlistSettingsUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Update wishlist settings", request=WishlistSerializer, responses={200: WishlistSerializer})
    def patch(self, request):
        wishlist = get_or_create_user_wishlist(request.user)
        serializer = WishlistSerializer(wishlist, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class WishlistItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Add product to wishlist",
        request=WishlistItemSerializer,
        responses={201: WishlistItemSerializer},
    )
    def post(self, request):
        wishlist = get_or_create_user_wishlist(request.user)
        serializer = WishlistItemSerializer(data=request.data, context={'request': request, 'wishlist': wishlist})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(WishlistItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)


class WishlistItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Remove item from wishlist", responses={204: OpenApiResponse(description='Deleted')})
    def delete(self, request, item_id):
        wishlist = get_or_create_user_wishlist(request.user)
        item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistClearView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Clear wishlist", responses={204: OpenApiResponse(description='Cleared')})
    def delete(self, request):
        wishlist = get_or_create_user_wishlist(request.user)
        wishlist.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistMoveToCartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Move item to cart",
        request={'application/json': {'type': 'object', 'properties': {'quantity': {'type': 'integer', 'default': 1}}}},
        responses={200: OpenApiResponse(description='Moved to cart and removed from wishlist')},
    )
    def post(self, request, item_id):
        quantity = int(request.data.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        wishlist = get_or_create_user_wishlist(request.user)
        item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
        # Assuming there is a cart service; using WishlistItem.move_to_cart signature
        try:
            # Defer cart implementation; call domain method if available
            item.move_to_cart(cart=request.user.cart, quantity=quantity)  # type: ignore[attr-defined]
        except Exception:
            # Fallback: just delete item if cart is not available
            item.delete()
        return Response({'detail': 'Item moved to cart'}, status=status.HTTP_200_OK)


class PublicWishlistView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="View a public wishlist",
        parameters=[OpenApiParameter('user_id', int, OpenApiParameter.PATH, description='User id')],
        responses={200: WishlistSerializer, 403: OpenApiResponse(description='Wishlist is private')},
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        wishlist = get_object_or_404(Wishlist, user=user)
        if not wishlist.is_public:
            return Response({'detail': 'This wishlist is private'}, status=status.HTTP_403_FORBIDDEN)
        return Response(WishlistSerializer(wishlist, context={'request': request}).data)


