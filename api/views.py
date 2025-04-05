from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Case, When, Value, FloatField
from django.db.models.functions import Concat
from .models import User, Contact, SpamReport
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    ContactSerializer,
    BulkContactSerializer,
    SpamReportSerializer,
    SearchResultSerializer,
)
class WelcomeView(APIView):
    def get(self, request):
        return Response({
            "message": "Welcome to Spam Detector API",
            "endpoints": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "contacts": "/api/contacts/",
                "spam_reports": "/api/spam-reports/",
                "search_by_name": "/api/search/?q=<name>",
                "search_by_phone": "/api/search/phone/?q=<phone>"
            }
        })

class UserRegistrationView(generics.CreateAPIView):
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)

from django.conf import settings

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response_data = {
            'token': access_token,
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'email': user.email
            }
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)

        from django.contrib.auth import login
        login(request, user)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG 
        )
        
        return response

class ContactListView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BulkContactCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BulkContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contacts_data = serializer.validated_data['contacts']
        contacts = [
            Contact(
                user=request.user,
                name=contact['name'],
                phone_number=contact['phone_number']
            ) for contact in contacts_data
        ]
        
        created_contacts = Contact.objects.bulk_create(contacts)
        
        return Response(
            ContactSerializer(created_contacts, many=True).data,
            status=status.HTTP_201_CREATED
        )

class SpamReportListView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    serializer_class = SpamReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SpamReport.objects.filter(reporter=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

class SearchByNameView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        search_query = request.query_params.get('q', '').strip().lower()
        if not search_query:
            return Response([], status=status.HTTP_200_OK)

        spam_counts = SpamReport.objects.values('phone_number').annotate(
            report_count=Count('phone_number')
        )
        
        total_users = User.objects.count()
        
        registered_users = User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name')
        ).filter(
            full_name__icontains=search_query
        ).annotate(
            spam_likelihood=Case(
                When(phone_number__in=[item['phone_number'] for item in spam_counts], 
                     then=Count('spamreport__phone_number') * 100.0 / total_users),
                default=Value(0.0),
                output_field=FloatField()
            )
        ).order_by(
            Case(
                When(full_name__istartswith=search_query, then=0),
                default=1
            ),
            'full_name'
        )
        contacts = Contact.objects.filter(
            name__icontains=search_query
        ).exclude(
            phone_number__in=User.objects.values('phone_number')
        ).annotate(
            spam_likelihood=Case(
                When(phone_number__in=[item['phone_number'] for item in spam_counts], 
                     then=Count('spamreport__phone_number') * 100.0 / total_users),
                default=Value(0.0),
                output_field=FloatField()
            )
        ).order_by(
            Case(
                When(name__istartswith=search_query, then=0),
                default=1
            ),
            'name'
        )

        results = []
        
        for user in registered_users:
            email = None
            if Contact.objects.filter(user=user, phone_number=request.user.phone_number).exists():
                email = user.email
                
            results.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'phone_number': user.phone_number,
                'spam_likelihood': user.spam_likelihood,
                'email': email
            })
        
        for contact in contacts:
            results.append({
                'id': None,
                'name': contact.name,
                'phone_number': contact.phone_number,
                'spam_likelihood': contact.spam_likelihood,
                'email': None
            })
        
        return Response(results, status=status.HTTP_200_OK)

class SearchByPhoneView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        phone_number = request.query_params.get('q', '').strip()
        if not phone_number:
            return Response([], status=status.HTTP_200_OK)

        total_users = User.objects.count()
        spam_reports = SpamReport.objects.filter(phone_number=phone_number).count()
        spam_likelihood = (spam_reports * 100.0 / total_users) if total_users > 0 else 0.0

        registered_users = User.objects.filter(phone_number=phone_number)
        if registered_users.exists():
            user = registered_users.first()

            email = None
            if Contact.objects.filter(user=user, phone_number=request.user.phone_number).exists():
                email = user.email
                
            return Response([{
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'phone_number': user.phone_number,
                'spam_likelihood': spam_likelihood,
                'email': email
            }], status=status.HTTP_200_OK)
            
        contacts = Contact.objects.filter(phone_number=phone_number)
        
        results = [{
            'id': None,
            'name': contact.name,
            'phone_number': contact.phone_number,
            'spam_likelihood': spam_likelihood,
            'email': None
        } for contact in contacts]
        
        return Response(results, status=status.HTTP_200_OK)