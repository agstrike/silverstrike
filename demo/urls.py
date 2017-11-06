from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView
from rest_framework import routers

from silverstrike import serializers as agss

router = routers.DefaultRouter()
router.register(r'accounts', agss.AccountList)
router.register(r'transactions', agss.Transactions)
router.register(r'splits', agss.Splits)
router.register(r'categories', agss.Categories)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('silverstrike.urls')),
    url(r'^rest/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
