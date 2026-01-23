from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

def rm_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/chat/inbox/")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def rm_logout(request):
    logout(request)
    return redirect(rm_login)
