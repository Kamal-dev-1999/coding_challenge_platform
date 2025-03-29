from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import CustomUser

User=CustomUser
from django.contrib.auth.models import User
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)  # Return only user id

    def validate(self, data):
        user = authenticate(**data)
        if user:
            refresh = RefreshToken.for_user(user)
            return {
                'username': user.username,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
            }
        raise serializers.ValidationError("Invalid credentials")

