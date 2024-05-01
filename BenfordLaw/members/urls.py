from django.urls import path
from . import views


urlpatterns = [
    path('hello',views.upload_excel2)
]

