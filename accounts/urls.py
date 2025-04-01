from django.urls import path
from .views import RegisterView, LoginView, auth_page, LogoutView, dashboard,ProfileView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/', auth_page, name='auth-page'),
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),  # Updated logout URL
    path('dashboard/', dashboard, name='dashboard'),  # Dashboard URL
    path('profile/', ProfileView.as_view(), name='profile'),  # Profile URL
]
