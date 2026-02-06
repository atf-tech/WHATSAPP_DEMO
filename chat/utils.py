import subprocess
import uuid
import os
from django.conf import settings


def convert_webm_to_ogg(uploaded_file):
    tmp_dir = os.path.join(settings.MEDIA_ROOT, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    uid = uuid.uuid4().hex

    webm_path = os.path.join(tmp_dir, f"{uid}.webm")
    ogg_path = os.path.join(tmp_dir, f"{uid}.ogg")

    # Save browser-recorded webm
    with open(webm_path, "wb+") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    # 🔥 WhatsApp-compliant conversion
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", webm_path,
            "-ac", "1",              # mono
            "-ar", "48000",           # 48kHz
            "-c:a", "libopus",
            "-b:a", "64k",
            "-application", "voip",   # 🔑 REQUIRED by WhatsApp
            ogg_path,
        ],
        check=True,
    )

    return webm_path, ogg_path
