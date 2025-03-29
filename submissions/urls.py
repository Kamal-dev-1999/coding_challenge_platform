# submissions/urls.py
from django.urls import path
from .views import (
    submission_history, 
    SubmissionCreateAPIView, SubmissionListAPIView
)

urlpatterns = [
    # HTML view endpoint
    path('history/', submission_history, name='submission-history'),

    # API endpoints
    path('api/create/', SubmissionCreateAPIView.as_view(), name='api-submission-create'),
    path('api/list/', SubmissionListAPIView.as_view(), name='api-submission-list'),
]
