from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("conversation/<int:convo_id>/", views.conversation, name="conversation"),
    path(
        "conversation/<int:convo_id>/messages/",
        views.messages_partial,
        name="messages-partial"
    ),
    path(
    "send-media/<int:convo_id>/",
    views.send_media_message,
    name="send-media-message"),

    path("send/<int:convo_id>/", views.send_message, name="send-message"),
    path("messages/<int:message_id>/react/", views.toggle_reaction, name="toggle-reaction")


]
