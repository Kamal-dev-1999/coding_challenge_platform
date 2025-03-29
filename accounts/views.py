from rest_framework import generics, permissions
from rest_framework.response import Response
from .seriazlizers import RegisterSerializer, LoginSerializer
from accounts.models import CustomUser
from django.contrib.auth import login
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Count
import json
from django.contrib.auth.decorators import login_required
from submissions.models import Submission

def auth_page(request):
    return render(request, "accounts/auth.html")

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Retrieve user using the returned user_id
        user_id = data.get('user_id')
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=400)
        # Log the user in so that request.user becomes authenticated
        login(request, user)
        # Save the generated token in the session (for client-side use)
        request.session['access_token'] = data['access']
        return Response(data)


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        return self.perform_logout(request)
        
    def get(self, request):  # Handle GET requests for browser links
        return self.perform_logout(request)

    def perform_logout(self, request):
        logout(request)
        request.session.flush()
        return redirect('auth-page')  # Redirect to the auth page after logout
    
    
@login_required
def dashboard(request):
    user = request.user
    submissions = Submission.objects.filter(user=user)
    
    # Aggregate submission counts by result
    stats = submissions.values('result').annotate(count=Count('result'))
    stats_dict = {s['result']: s['count'] for s in stats}
    
    accepted = stats_dict.get('Accepted', 0)
    wrong = stats_dict.get('Wrong Answer', 0)
    runtime = stats_dict.get('Runtime Error', 0)
    total = submissions.count()
    
    context = {
        'accepted': accepted,
        'wrong': wrong,
        'runtime': runtime,
        'total': total,
        # Pass the stats as JSON if needed for advanced charting
        'stats_json': json.dumps(stats_dict)
    }
    
    return render(request, 'accounts/dashboard.html', context)