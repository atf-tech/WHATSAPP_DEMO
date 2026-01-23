from django.urls import path
from . import views

urlpatterns = [
    path("", views.rm_login, name="login"),
    path("logout/", views.rm_logout, name="logout"),
]
