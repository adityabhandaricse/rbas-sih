from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Standard API prefix (e.g., /api/feasibility/)
    path('api/', include('core_app.urls')),

    # Versioned API prefix (e.g., /api/v1/feasibility/generate/)
    path('api/v1/', include('core_app.urls')),
]