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

    with open(webm_path, "wb+") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v", "error",
            "-i", webm_path,
            "-c:a", "libopus",
            "-b:a", "64k",
            ogg_path,
        ],
        check=True,
    )

    return webm_path, ogg_path


