from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from .views import predict_price

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version='v1',
        description="API Documentation",
    ),
    public=True,
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('predict_price/', predict_price),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # path('train/', get_my_table, name='get_my_table'),
]
