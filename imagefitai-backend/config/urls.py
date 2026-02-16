from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('jobs.urls')),
]

def rate_limit_exceeded(request, exception):
    return JsonResponse({
        'error': 'Rate limit exceeded. Please try again later.',
        'limit_reached': True
    }, status=429)

handler429 = rate_limit_exceeded