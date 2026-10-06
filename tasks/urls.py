from django.urls import path
from . import views # import views from same folder

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("health/", views.health, name="health"),
    path("tasks/<int:task_id>/", views.get_task, name="task_detail"),
]