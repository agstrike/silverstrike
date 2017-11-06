from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
 
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
 
 
class AlwaysAuthenticatedMiddleware(MiddlewareMixin):
    """
    Ensures that the request has an authenticated user.
 
    If the request doesn't have an authenticated user, it logs in a default
    user. If the default user doesn't exist, it is created.
 
    Will raise an ImproperlyConfiguredException when DEBUG=False, unless
    ALWAYS_AUTHENTICATED_DEBUG_ONLY is set to False.
 
    This middleware reads these settings:
    * ALWAYS_AUTHENTICATED_USERNAME (string):
      the name of the default user, defaults to `'user'`.
    * ALWAYS_AUTHENTICATED_USER_DEFAULTS (dict):
      additional default values to set when creating the user.
    * ALWAYS_AUTHENTICATED_DEBUG_ONLY:
      Set to `False` to allow running with DEBUG=False.
    """
    def __init__(self, *args, **kwargs):
 
        self.username = getattr(settings,
                                'ALWAYS_AUTHENTICATED_USERNAME',
                                'user')
        self.defaults = getattr(settings,
                                'ALWAYS_AUTHENTICATED_USER_DEFAULTS',
                                {})
        if (not settings.DEBUG and
                getattr(settings,'ALWAYS_AUTHENTICATED_DEBUG_ONLY', True)):
            raise ImproperlyConfigured(
                'DEBUG=%s, but AlwaysAuthenticatedMiddleware is configured to '
                'only run in debug mode.\n'
                'Remove AlwaysAuthenticatedMiddleware from '
                'MIDDLEWARE/MIDDLEWARE_CLASSES or set '
                'ALWAYS_AUTHENTICATED_DEBUG_ONLY to False.' % settings.DEBUG)
        super(AlwaysAuthenticatedMiddleware, self).__init__(*args, **kwargs)
 
    def process_request(self, request):
        if not request.user.is_authenticated():
            user, created = User.objects.get_or_create(username=self.username,
                                                       defaults=self.defaults)
 
            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user)
