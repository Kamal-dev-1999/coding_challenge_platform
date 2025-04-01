from .views import *
from django.urls import path



urlpatterns = [
    path('competitiors/', AllCompetitorsPorfileView.as_view(), name='competitors'),
    path('competitor/<int:user_id>/', CompetitorProfileView.as_view(), name='competitor_profile'),
]
