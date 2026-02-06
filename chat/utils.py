import subprocess
import uuid
import os
from django.conf import settings

def convert_webm_to_ogg(file_obj):
    tmp_dir = os.path.join(settings.MEDIA_ROOT, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    uid = uuid.uuid4().hex
    webm_path = os.path.join(tmp_dir, f"{uid}.webm")
    ogg_path = os.path.join(tmp_dir, f"{uid}.ogg")

    # 🔥 Save input file safely
    with open(webm_path, "wb") as out:
        if hasattr(file_obj, "chunks"):
            # UploadedFile
            for chunk in file_obj.chunks():
                out.write(chunk)
        else:
            # FileField / file on disk
            file_obj.open("rb")
            out.write(file_obj.read())
            file_obj.close()

    # 🔥 WhatsApp-compliant conversion
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", webm_path,
            "-ac", "1",
            "-ar", "48000",
            "-c:a", "libopus",
            "-b:a", "64k",
            "-application", "voip",
            ogg_path,
        ],
        check=True,
    )

    return webm_path, ogg_path
