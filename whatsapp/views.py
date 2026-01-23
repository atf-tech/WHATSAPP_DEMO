import json
import random
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import RM
from chat.models import Donor, Conversation, Message

VERIFY_TOKEN = "demo_verify_token" 


@csrf_exempt
def webhook(request):
    if request.method == "GET":
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse("Invalid token", status=403)

    if request.method == "POST":
        payload = json.loads(request.body)

        try:
            value = payload["entry"][0]["changes"][0]["value"]
            msg = value["messages"][0]

            donor_number = msg["from"]
            text = msg["text"]["body"]
        except Exception:
            return JsonResponse({"status": "ignored"})

        donor, _ = Donor.objects.get_or_create(
            phone_number=donor_number
        )

        conversation = Conversation.objects.filter(
            donor=donor,
            status="open"
        ).first()

        if not conversation:
            rm = random.choice(
                RM.objects.filter(is_active=True)
            )
            conversation = Conversation.objects.create(
                donor=donor,
                rm=rm
            )

        Message.objects.create(
            conversation=conversation,
            direction="in",
            body=text
        )

        return JsonResponse({"status": "ok"})

