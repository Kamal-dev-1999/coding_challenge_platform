# problems/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from rest_framework import generics
from .models import Problem
from .serializers import ProblemSerializer
from submissions.models import Submission
from .utlis import evaluate_submission
from django.contrib.auth.decorators import login_required
# --- API endpoints using DRF ---
# API endpoint to list all problems
class ProblemListAPIView(generics.ListAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

# API endpoint to get details of a specific problem
class ProblemDetailAPIView(generics.RetrieveAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

# --- HTML views below ---
@login_required(login_url='auth-page')
def load_base_template(request):
    # Load the base template and include the token in context
    token = request.session.get('access_token')
    return render(request, 'problems/base.html', {'token': token})

@login_required(login_url='auth-page')
def problem_list(request):
    token = request.session.get('access_token')
    if not token:
        # Redirect to the auth page if the token is not available
        return redirect('auth-page')
    problems = Problem.objects.all()
    # Print statements for debugging (remove in production)
    print(problems)
    print(token)
    return render(request, 'problems/problem_list.html', {'problems': problems, 'token': token})


@login_required(login_url='auth-page')
def problem_detail(request, pk):
    token = request.session.get('access_token')
    if not token:
        return redirect('auth-page')
    problem = get_object_or_404(Problem, pk=pk)
    return render(request, 'problems/problem_detail.html', {'problem': problem, 'token': token})


@login_required(login_url='auth-page')
def submit_solution(request, pk):
    token = request.session.get('access_token')
    if not token:
        return redirect('auth-page')
    problem = get_object_or_404(Problem, pk=pk)
    if request.method == 'POST':
        user_code = request.POST.get('code')
        # Evaluate the submission using the utility function
        result, message = evaluate_submission(user_code, problem)
        # Save the submission (assuming the user is logged in)
        Submission.objects.create(user=request.user, problem=problem, code=user_code, result=result)
        return render(request, 'problems/submission_result.html', {
            'problem': problem,
            'result': result,
            'message': message,
            'code': user_code,
            'token': token
        })
    # For GET requests, redirect back to the problem detail page.
    return redirect(reverse('problem-detail', args=[pk]))
