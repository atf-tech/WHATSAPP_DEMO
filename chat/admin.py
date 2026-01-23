from django.contrib import admin
from .models import Donor, Conversation, Message

admin.site.register(Donor)
admin.site.register(Conversation)
admin.site.register(Message)
