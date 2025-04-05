from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    
    username = None
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    def clean(self):
        super().clean()

        if not re.match(r'^\+[1-9]\d{1,14}$', self.phone_number):
            raise ValidationError({'phone_number': 'Phone number must be in E.164 format (e.g., +11234567890)'})

        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError({'email': 'Enter a valid email address'})


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    
    class Meta:
        unique_together = ('user', 'phone_number')
    
    def clean(self):
        if not re.match(r'^\+[1-9]\d{1,14}$', self.phone_number):
            raise ValidationError({'phone_number': 'Phone number must be in E.164 format (e.g., +11234567890)'})

class SpamReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spam_reports')
    phone_number = models.CharField(max_length=15)
    reported_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('reporter', 'phone_number')
    
    def clean(self):
        if not re.match(r'^\+[1-9]\d{1,14}$', self.phone_number):
            raise ValidationError({'phone_number': 'Phone number must be in E.164 format (e.g., +11234567890)'})