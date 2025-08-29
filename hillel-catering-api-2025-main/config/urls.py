from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from food.views import import_dishes, kfc_webhook
from food.views import router as food_router
from food.views import UberWebhookView, CourierLocationView
from users.views import router as users_router

urlpatterns = [
    path("admin/food/dish/import-dishes/", import_dishes, name="import_dishes"),
    path("admin/", admin.site.urls),

    path("auth/token/", TokenObtainPairView.as_view(), name="obtain_token"),

    path("users/", include(users_router.urls)),
    path("food/", include(food_router.urls)),

    path(
        "webhooks/kfc/5834eb6c-63b9-4018-b6d3-04e170278ec2/",
        kfc_webhook,
    ),
    path("api/uber/webhook/", UberWebhookView.as_view()),
    path("api/courier/location/", CourierLocationView.as_view()),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]

if settings.DEBUG:
    urlpatterns += [
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]
