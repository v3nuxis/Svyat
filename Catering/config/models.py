from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# class User(models.Model):
#     ROLE_CHOICES = [
#         ("admin", "Admin"),
#         ("customer", "Customer"),
#         ("driver", "Driver"),
#         ("support", "Support"),
#     ]

#     name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=20)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customer")

#     def __str__(self):
#         return self.name


# class Dish(models.Model):
#     name = models.CharField(max_length=100)
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return self.name


# class Order(models.Model):
#     STATUS_CHOICES = [
#         ("pending", "Pending"),
#         ("completed", "Completed"),
#         ("cancelled", "Cancelled"),
#     ]

#     date = models.DateField()
#     total = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
#     user = models.ForeignKey(User, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"Order {self.id} by {self.user.name}"


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE)
#     dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()

#     def __str__(self):
#         return f"{self.quantity} x {self.dish.name} in Order {self.order.id}"



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

class User(AbstractBaseUser, PermissionError):
    ROLE_CHOICES = {
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('support', 'Support'),
    }
    
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()
    Username_objects = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']
    
    def __str__(self):
        return self.email
    