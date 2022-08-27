from rest_framework import permissions

from silverstrike.models import AccountType


class ProtectSystemAccount(permissions.BasePermission):
    def has_object_permission(self, request, view, object):
        if request.method in permissions.SAFE_METHODS:
            return True
        return object.account_type != AccountType.SYSTEM
