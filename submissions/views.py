# submissions/views.py
from rest_framework import generics, permissions
from .models import Submission
from .serializers import SubmissionSerializer

# API endpoint to create a submission
class SubmissionCreateAPIView(generics.CreateAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

# API endpoint to list the current user's submissions
class SubmissionListAPIView(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)

# --- HTML view for submission history ---
from django.shortcuts import render

def submission_history(request):
    submissions = Submission.objects.filter(user=request.user)
    return render(request, 'submissions/submission_history.html', {'submissions': submissions})
