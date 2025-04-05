from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Contact, SpamReport
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['phone_number'] = user.phone_number
        return token

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['phone_number'],
            password=attrs['password']
        )
        
        if not user:
            raise serializers.ValidationError('Invalid credentials')
            
        return {'user': user}

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number']
        read_only_fields = ['id']

class BulkContactSerializer(serializers.Serializer):
    contacts = ContactSerializer(many=True)

class SpamReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpamReport
        fields = ['id', 'phone_number', 'reported_at']
        read_only_fields = ['id', 'reported_at']

class SearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    phone_number = serializers.CharField()
    spam_likelihood = serializers.FloatField()
    email = serializers.EmailField(required=False, allow_null=True)