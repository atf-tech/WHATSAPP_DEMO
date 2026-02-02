import requests
from django.conf import settings


HEADERS = {
    "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
}


def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{settings.WA_PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return res.json()


# ===============================
# 🔥 MEDIA SUPPORT (ALL TYPES)
# ===============================

def upload_media_to_whatsapp(file_path, mime_type):
    url = f"https://graph.facebook.com/v18.0/{settings.WA_PHONE_NUMBER_ID}/media"

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path, f, mime_type),
            "messaging_product": (None, "whatsapp"),
        }

        res = requests.post(url, headers=HEADERS, files=files, timeout=20)
        res.raise_for_status()
        return res.json()["id"]


def send_whatsapp_media_message(to, media_id, media_type, caption=None):

    url = f"https://graph.facebook.com/v18.0/{settings.WA_PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": media_type,
        media_type: {
            "id": media_id
        }
    }

    if caption and media_type in ["image", "video", "document"]:
        payload[media_type]["caption"] = caption

    res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return res.json()
