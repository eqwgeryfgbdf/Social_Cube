from django.shortcuts import render
from django.http import JsonResponse

def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Social Cube API',
        'version': '1.0.0'
    })
