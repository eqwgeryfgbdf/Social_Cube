from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Bot, BotLog
from .serializers import BotSerializer, BotDetailSerializer, BotLogSerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a bot to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner
        return obj.owner == request.user

class BotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Bot management
    """
    serializer_class = BotSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Filter bots to return only those owned by the current user"""
        return Bot.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for list and detail"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return BotDetailSerializer
        return BotSerializer
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        Toggle the is_active status of a bot
        """
        bot = self.get_object()
        bot.is_active = not bot.is_active
        bot.save()
        
        # Log the status change
        status_text = "activated" if bot.is_active else "deactivated"
        BotLog.objects.create(
            bot=bot,
            event_type=f'BOT_{status_text.upper()}',
            description=f'Bot {status_text} by {request.user.username} via API'
        )
        
        serializer = self.get_serializer(bot)
        return Response({
            'status': 'success',
            'message': f'Bot {status_text} successfully',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Retrieve logs for a specific bot
        """
        bot = self.get_object()
        logs = bot.logs.all().order_by('-timestamp')
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = BotLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = BotLogSerializer(logs, many=True)
        return Response(serializer.data)

class BotLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for BotLog (read-only)
    """
    serializer_class = BotLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter logs to return only those for bots owned by the current user"""
        return BotLog.objects.filter(bot__owner=self.request.user).order_by('-timestamp')