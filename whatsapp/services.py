import requests
from django.conf import settings


def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{settings.WA_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {
            "error": True,
            "details": str(e)
        }
