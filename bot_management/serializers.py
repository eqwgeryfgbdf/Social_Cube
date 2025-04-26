from rest_framework import serializers
from .models import Bot, BotLog

class BotSerializer(serializers.ModelSerializer):
    """Serializer for Bot model"""
    owner_username = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Bot
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'client_id', 'bot_user_id', 'avatar_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Assign current user as owner
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class BotDetailSerializer(BotSerializer):
    """Detailed serializer for Bot model with token field"""
    
    class Meta(BotSerializer.Meta):
        fields = BotSerializer.Meta.fields + ['token']
    
    def to_representation(self, instance):
        # Don't return the actual token in API responses for security
        representation = super().to_representation(instance)
        representation['token'] = '•••••••••••••••••' # Mask the token
        return representation

class BotLogSerializer(serializers.ModelSerializer):
    """Serializer for BotLog model"""
    bot_name = serializers.ReadOnlyField(source='bot.name')
    
    class Meta:
        model = BotLog
        fields = ['id', 'bot', 'bot_name', 'event_type', 'description', 'timestamp']
        read_only_fields = ['id', 'timestamp']