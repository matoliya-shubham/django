from django.urls import path
from . import views # import views from same folder

urlpatterns = [
    path("ping/", views.ping, name="ping")
]