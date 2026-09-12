from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings

def serve_frontend(request):
    dist_index = Path(settings.BASE_DIR).parent / 'frontend' / 'dist' / 'index.html'
    if dist_index.exists():
        with open(dist_index, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse(
        "<h1>AdosX API is running. Build frontend with 'npm run build' inside frontend/ directory.</h1>",
        content_type='text/html'
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reconciler.urls')),
    re_path(r'^(?!api/|admin/).*$', serve_frontend),
]
