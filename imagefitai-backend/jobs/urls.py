from django.urls import path
from django.http import JsonResponse
from .views import PresignedUploadView, JobCreateView, JobStatusView


def health(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('uploads/presign', PresignedUploadView.as_view(), name='presigned-upload'),
    path('jobs', JobCreateView.as_view(), name='job-create'),
    path('jobs/health', health, name='health'),
    path('jobs/<uuid:job_id>', JobStatusView.as_view(), name='job-status'),
]