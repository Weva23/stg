
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('consultants.urls')),  # Inclusion des routes de mon_app
path('api/', include('consultants.urls'))

]

