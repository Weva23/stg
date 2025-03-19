from django.urls import path
from .views import UploadCV

urlpatterns = [
    path('upload-cv/', UploadCV.as_view(), name='upload-cv'),
]
