from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = {
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('support', 'Support'),
    }
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    
class UserManager(BaseUserManager):
    def creating_user(self, email, first_name, last_name, phone, password = None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'customer')
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def creating_superuser(self, email, phone, password = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.creating_user(email, phone, password, **extra_fields)
    
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    Username_objects = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']
    
    def __str__(self):
        return self.email
    