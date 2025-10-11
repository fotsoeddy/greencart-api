# /home/eddy/projects/shella/green_cart/green_cart_api/config/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/', include('green_cart_api.users.urls', namespace='users')),
    path('api/catalog/', include('green_cart_api.catalog.urls', namespace='catalog')),
    path('api/wishlist/', include('green_cart_api.wishlist.urls', namespace='wishlist')),
    path('api/carts/', include('green_cart_api.cart.urls', namespace='carts')),
    path('api/orders/', include('green_cart_api.order.urls', namespace='orders')),
    path('accounts/', include('allauth.urls')),
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name='api-schema',
    ),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='api-schema',
            permission_classes=[AllowAny],
        ),
        name='api-docs',
    ),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# Development error pages
if settings.DEBUG:
    urlpatterns += [
        path('400/', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        path('403/', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        path('404/', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        path('500/', default_views.server_error),
    ]
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), *urlpatterns]