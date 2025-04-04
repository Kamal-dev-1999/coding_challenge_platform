# problems/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from rest_framework import generics, filters
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Problem
from .serializers import ProblemSerializer
from submissions.models import Submission
from .utlis import evaluate_submission, safe_exec, parse_value
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from submissions.models import Submission
import json
from django.views.decorators.http import require_http_methods

# --- API endpoints using DRF ---
# API endpoint to list all problems
class ProblemListAPIView(generics.ListAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['difficulty', 'created_at']
    ordering = ['-created_at']

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

    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    difficulty = request.GET.get('difficulty', '')
    page = request.GET.get('page', 1)
    per_page = 12  # Number of problems per page

    # Base queryset
    problems = Problem.objects.all()

    # Apply search filter
    if search_query:
        problems = problems.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Apply difficulty filter
    if difficulty:
        problems = problems.filter(difficulty=difficulty)

    # Get featured problems (problems with most submissions)
    featured_problems = Problem.objects.annotate(
        submission_count=Count('submission')
    ).order_by('-submission_count')[:3]

    # Paginate the problems
    paginator = Paginator(problems, per_page)
    problems_page = paginator.get_page(page)

    context = {
        'problems': problems_page,
        'featured_problems': featured_problems,
        'search_query': search_query,
        'difficulty': difficulty,
        'token': token,
        'difficulty_choices': Problem.DIFFICULTY_CHOICES,
    }
    return render(request, 'problems/problem_list.html', context)

@login_required(login_url='auth-page')
def problem_detail(request, pk):
    token = request.session.get('access_token')
    if not token:
        return redirect('auth-page')
    
    problem = get_object_or_404(Problem, pk=pk)
    
    # Get related problems (same difficulty)
    related_problems = Problem.objects.filter(
        difficulty=problem.difficulty
    ).exclude(pk=pk)[:3]

    # Get user's previous submissions for this problem
    user_submissions = Submission.objects.filter(
        user=request.user,
        problem=problem
    )

    context = {
        'problem': problem,
        'related_problems': related_problems,
        'user_submissions': user_submissions,
        'token': token
    }
    return render(request, 'problems/problem_detail.html', context)

@login_required(login_url='auth-page')
def submit_solution(request, pk):
    token = request.session.get('access_token')
    if not token:
        return redirect('auth-page')
    
    problem = get_object_or_404(Problem, pk=pk)
    
    if request.method == 'POST':
        user_code = request.POST.get('code')
        
        # Evaluate the submitted code using the utlis.py functions.
        try:
            # evaluate_submission returns a tuple: (result, message, detailed_results)
            result, message, detailed_results = evaluate_submission(user_code, problem)
        except Exception as e:
            # Catch any unexpected errors during evaluation
            result = "System Error"
            message = f"An error occurred during code evaluation: {str(e)}"
            detailed_results = None

        # Save the submission (even if evaluation failed, you may want to keep a record)
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=user_code,
            result=result
        )

        # If the request is AJAX, return a JSON response with details
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'result': result,
                'message': message,
                'details': detailed_results,
                'submission_id': submission.id
            })

        # Otherwise, render a results page
        return render(request, 'problems/submission_result.html', {
            'problem': problem,
            'result': result,
            'message': message,
            'details': detailed_results,
            'code': user_code,
            'token': token
        })
    
    return redirect(reverse('problem-detail', args=[pk]))


# API endpoint for real-time search
@login_required(login_url='auth-page')
def search_problems(request):
    query = request.GET.get('q', '')
    if query:
        problems = Problem.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        data = [{'id': p.id, 'title': p.title, 'difficulty': p.difficulty} for p in problems]
    else:
        data = []
    return JsonResponse({'results': data})

from django.shortcuts import get_object_or_404
# ... other imports ...

@require_http_methods(["POST"])
@login_required
def run_test(request, problem_id):
    try:
        data = json.loads(request.body)
        code = data.get('code')
        test_input = data.get('input')
        
        # Log the received payload for debugging
        print("run_test received code:", code)
        print("run_test received input:", test_input)
        
        # Get the problem object
        problem = get_object_or_404(Problem, pk=problem_id)
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Code is required'
            })
        
        # If no test input provided, use the problem's sample input
        if not test_input:
            test_input = problem.sample_input
            print("No input provided. Using sample input:", test_input)
        
        # Parse the input using the util function
        parsed_input = parse_value(test_input)
        print("Parsed input:", parsed_input)
        
        # Execute the user code safely
        result, stdout, execution_time, success, error = safe_exec(code, parsed_input)
        print("Execution result:", result, "Success:", success)
        
        if success:
            return JsonResponse({
                'success': True,
                'output': str(result),
                'stdout': stdout,
                'execution_time': execution_time
            })
        else:
            return JsonResponse({
                'success': False,
                'error': error
            })
            
    except Exception as e:
        print("Error in run_test:", str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
