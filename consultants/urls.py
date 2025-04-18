
from django.urls import path
from . import views

urlpatterns = [
    path('consultant/register/', views.consultant_register, name='consultant-register'),
    path('consultant/login/', views.consultant_login, name='consultant-login'),
    path('consultant/<int:consultant_id>/data/', views.consultant_data, name='consultant-data'),
    path('consultant/<int:consultant_id>/competences/', views.consultant_competences, name='consultant-competences'),
]
