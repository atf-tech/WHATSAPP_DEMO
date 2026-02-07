from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os
from django.http import FileResponse, Http404

def service_worker(request):
    path = os.path.join(settings.BASE_DIR, "service-worker.js")
    if not os.path.exists(path):
        raise Http404("service-worker.js not found")
    return FileResponse(open(path, "rb"), content_type="application/javascript")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("whatsapp/", include("whatsapp.urls")),
    path("chat/", include("chat.urls")),
    path("service-worker.js", service_worker),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
