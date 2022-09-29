from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


# This Plugin is used for the demo to automatically authenticate all requests.
# You can use this as a starting point if you handle authentication in a reverse proxy before silverstrike
# You need to include this middleware in your settings override after the django authentication middleware
class AlwaysAuthenticatedMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            user, created = User.objects.get_or_create(username='demo')
            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user)


