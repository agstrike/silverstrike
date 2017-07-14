from django.conf.urls import include, url
from django.views.generic import TemplateView


from . import api, views
from .models import Account


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^auth/', include('allauth.urls')),

    url(r'^transactions/transfer/create$',
        views.TransferCreate.as_view(), name='transfer_new'),
    url(r'^transactions/withdraw/create$',
        views.WithdrawCreate.as_view(), name='withdraw_new'),
    url(r'^transactions/deposit/create$',
        views.DepositCreate.as_view(), name='deposit_new'),

    url(r'^transactions/edit/(?P<pk>\d+)$',
        views.TransferUpdate.as_view(), name='transaction_update'),

    url(r'^categories$', views.CategoryIndex.as_view(), name='categories'),
    url(r'^charts$', views.ChartView.as_view(), name='charts'),

    url(r'^transactions/$', views.TransactionIndex.as_view(), name='transactions'),
    url(r'^accounts/(?P<pk>\d+)/(?P<dstart>\S+)/$',
        views.AccountView.as_view(), name='account_detail'),

    url(r'^recurrances/$', views.RecurringTransactionIndex.as_view(), name='recurrances'),

    url(r'^accounts/new$', views.AccountCreate.as_view(), name='account_new'),
    url(r'^accounts/personal$',
        views.AccountIndex.as_view(account_type=Account.PERSONAL), name='personal_accounts'),
    url(r'^accounts/expense$',
        views.AccountIndex.as_view(account_type=Account.EXPENSE), name='expense_accounts'),
    url(r'^accounts/revenue$',
        views.AccountIndex.as_view(account_type=Account.REVENUE), name='revenue_accounts'),
    url(r'^accounts/update/(?P<pk>\d+)$', views.AccountUpdate.as_view(), name='account_update'),

    url(r'^api/accounts/(?P<account_type>\w+)$', api.get_accounts, name='api_accounts'),
    url(r'^api/accounts_balance/(?P<dstart>\S+)/(?P<dend>\S+)/$',
        api.get_accounts_balance, name='api_accounts_balance'),
    url(r'^manifest.json$', TemplateView.as_view(template_name='pyaccountant/manifest.json'),
        name='manifest'),

    url(r'^import/$', views.ImportView.as_view(), name='import'),
    url(r'^import/firefly/$', views.ImportFireflyView.as_view(), name='import_firefly'),
    url(r'^import/generic$', views.ImportUploadView.as_view(), name='import_generic'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/$', views.ImportConfigureView.as_view(),
        name='import_configure'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/process/(?P<config_pk>\d+)/$',
        views.ImportProcessView.as_view(), name='import_process'),
]
