from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('_nested_admin/', include('nested_admin.urls')),
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]
