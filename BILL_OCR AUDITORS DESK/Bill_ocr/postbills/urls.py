from django.urls import path
from . import views

# process_queued_file()

urlpatterns = [
    path('hello',views.ocr)
]

