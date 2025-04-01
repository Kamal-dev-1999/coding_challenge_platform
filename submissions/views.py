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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Submission
from problems.models import Problem
from django.db.models import Q

@login_required(login_url='auth-page')
def submission_history(request):
    token = request.session.get('access_token')
    if not token:
        return redirect('auth-page')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    problem_filter = request.GET.get('problem', '')
    page = request.GET.get('page', 1)
    per_page = 5  # Number of submissions per page
    
    # Get user's submissions
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    
    # Apply filters if provided
    if status_filter and status_filter != 'all':
        submissions = submissions.filter(result__icontains=status_filter)
    
    if problem_filter and problem_filter != 'all':
        submissions = submissions.filter(problem__title__icontains=problem_filter)
    
    # Get unique problems for the filter dropdown
    problems = Problem.objects.all()
    print(problems)
    # Paginate the submissions
    paginator = Paginator(submissions, per_page)
    page_obj = paginator.get_page(page)
    
    context = {
        'submissions': page_obj,
        'problems': problems,
        'token': token,
        'status_filter': status_filter,
        'problem_filter': problem_filter,
        'total_submissions': submissions.count(),
    }
    return render(request, 'submissions/submission_history.html', context)
