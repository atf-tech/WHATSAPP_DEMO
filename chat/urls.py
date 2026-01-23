from django.urls import path
from . import views

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("conversation/<int:convo_id>/", views.conversation, name="conversation"),
    path(
        "conversation/<int:convo_id>/messages/",
        views.messages_partial,
        name="messages-partial"
    ),
    path("send/<int:convo_id>/", views.send_message, name="send-message"),

]
