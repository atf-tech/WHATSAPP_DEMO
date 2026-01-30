from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse


def rm_login(request):

    # Already logged in → go to inbox
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
