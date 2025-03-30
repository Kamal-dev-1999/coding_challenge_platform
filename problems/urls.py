# problems/urls.py
from django.urls import path
from .views import (
    problem_list,
    problem_detail,
    submit_solution,  # Import the new view
    ProblemListAPIView,
    ProblemDetailAPIView,
    load_base_template,  # Import the base template loader
    run_test,
)

urlpatterns = [
    # HTML view endpoints,
    path('base/', load_base_template, name='base-template'),
    path('list/', problem_list, name='problem-list'),
    path('<int:pk>/', problem_detail, name='problem-detail'),
    path('<int:pk>/submit/', submit_solution, name='submit-solution'),
    
    # API endpoints
    path('api/', ProblemListAPIView.as_view(), name='api-problem-list'),
    path('api/<int:pk>/', ProblemDetailAPIView.as_view(), name='api-problem-detail'),
    path('api/run-test/<int:problem_id>/', run_test, name='run-test'),
]
