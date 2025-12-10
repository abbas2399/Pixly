from django.urls import path
from .views import PresignedUploadView, JobCreateView, JobStatusView

urlpatterns = [
    path('uploads/presign', PresignedUploadView.as_view(), name='presigned-upload'),
    path('jobs', JobCreateView.as_view(), name='job-create'),
    path('jobs/<uuid:job_id>', JobStatusView.as_view(), name='job-status'),
]