import time
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class IdleTimeoutMiddleware:
    """
    Logs out user after IDLE_TIMEOUT seconds of inactivity
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            last_activity = request.session.get("last_activity")

            if last_activity:
                idle_time = now - last_activity

                if idle_time > settings.IDLE_TIMEOUT:
                    # 🔥 Logout user
                    from django.contrib.auth import logout
                    logout(request)     
                    return redirect(reverse("rm_login"))

            # 🔄 Update activity timestamp
            request.session["last_activity"] = now

        response = self.get_response(request)
        return response
