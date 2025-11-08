from django.shortcuts import render
from .models import TeamMember

def team_list(request):
    members = TeamMember.objects.filter(is_active=True)
    return render(request, "team/list.html", {"members": members})
