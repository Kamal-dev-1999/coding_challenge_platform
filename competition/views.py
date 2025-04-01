from django.shortcuts import render
from accounts.models import CustomUser, Profile
from accounts.seriazlizers import ProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
import json
from submissions.models import Submission

# Create your views here.

class AllCompetitorsPorfileView(APIView):
    def get(self, request, format=None):
        profiles = Profile.objects.all()
        print("Profiles retrieved:", profiles)  # Debug statement
        serializer = ProfileSerializer(profiles, many=True)
        print("Serialized data:", serializer.data)  # Debug statement
        return render(request, 'competition/competitors.html', {'profiles': serializer.data})
    
class CompetitorProfileView(APIView):
    def get(self, request, user_id, format=None):
        try:
            # Get the competitor's profile based on user id
            profile = Profile.objects.get(user__id=user_id)
            serializer = ProfileSerializer(profile)
            
            # Gather submission statistics for this competitor
            submissions = Submission.objects.filter(user=profile.user)
            stats = submissions.values('result').annotate(count=Count('result'))
            stats_dict = {s['result']: s['count'] for s in stats}
            accepted = stats_dict.get('Accepted', 0)
            wrong = stats_dict.get('Wrong Answer', 0)
            runtime = stats_dict.get('Runtime Error', 0)
            total = submissions.count()
            recent_submissions = submissions.order_by('-submitted_at')[:5]
            context = {
                'profile': serializer.data,
                'accepted': accepted,
                'wrong': wrong,
                'runtime': runtime,
                'total': total,
                'stats_json': json.dumps(stats_dict),
                'recent_submissions': recent_submissions,
            }
            
            return render(request, 'competition/competitor_profile.html', context)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)