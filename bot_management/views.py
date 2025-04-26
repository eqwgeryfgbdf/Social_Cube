from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    """Bot management index view"""
    return render(request, 'bot_management/index.html', {
        'title': 'Bot Management'
    })
