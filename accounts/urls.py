from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path("", views.rm_login, name="rm_login"),
    path("logout/", views.rm_logout, name="rm_logout"),
    path("save-push/", push_subscribe, name="push_subscribe"),
]
