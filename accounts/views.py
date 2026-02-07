from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse


def rm_login(request):

    if request.user.is_authenticated:
        return redirect("/chat/inbox/")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.POST.get("next") or request.GET.get("next")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid username or password")
        else:
            # 🔐 Ensure user is an RM
            if not hasattr(user, "rm"):
                messages.error(request, "You are not authorized to access this system")
            else:
                login(request, user)
                return redirect(next_url or "/chat/inbox/")

    return render(request, "accounts/login.html")


def rm_logout(request):
    logout(request)
    return redirect(reverse("rm_login"))


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import PushSubscription


@csrf_exempt
@login_required
def push_subscribe(request):
    """
    Called ONCE after RM login.
    Saves browser push subscription.
    Logout does NOT affect delivery.
    """
    try:
        data = json.loads(request.body)

        sub = data.get("subscription")
        if not sub:
            return JsonResponse({"error": "missing_subscription"}, status=400)

        keys = sub.get("keys", {})
        endpoint = sub.get("endpoint")

        if not endpoint or "p256dh" not in keys or "auth" not in keys:
            return JsonResponse({"error": "invalid_subscription"}, status=400)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "rm": request.user.rm,
                "p256dh": keys["p256dh"],
                "auth": keys["auth"],
                "user_agent": request.META.get("HTTP_USER_AGENT", "")
            }
        )

        return JsonResponse({"status": "ok"})

    except Exception:
        return JsonResponse({"error": "push_subscribe_failed"}, status=400)
