from rest_framework import BasePermission

class IsAdminUserRole(BasePermission):
    def has_permission(BasePermission):
        return request.user.is_authenticated or request.user.role == "ADMIN"