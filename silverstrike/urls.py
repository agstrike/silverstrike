from django.conf.urls import include, url
from django.views.generic import TemplateView


from . import api, views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^auth/', include('allauth.urls')),

    url(r'^transactions/$', views.TransactionIndex.as_view(), name='transactions'),
    url(r'^transactions/(?P<pk>\d+)/$',
        views.TransactionDetailView.as_view(), name='transaction_detail'),
    url(r'^transactions/(?P<pk>\d+)/update/$',
        views.TransactionUpdateView.as_view(), name='transaction_update'),
    url(r'^transactions/(?P<pk>\d+)/split/$',
        views.SplitUpdate.as_view(), name='split_update'),
    url(r'^transactions/(?P<pk>\d+)/delete/$',
        views.TransactionDeleteView.as_view(), name='transaction_delete'),
    url(r'^transactions/create/transfer/$',
        views.TransferCreate.as_view(), name='transfer_new'),
    url(r'^transactions/create/withdraw/$',
        views.WithdrawCreate.as_view(), name='withdraw_new'),
    url(r'^transactions/create/deposit/$',
        views.DepositCreate.as_view(), name='deposit_new'),
    url(r'^transactions/create/split/$',
        views.SplitCreate.as_view(), name='split_create'),

    url(r'^accounts/(?P<pk>\d+)/update/$', views.AccountUpdate.as_view(), name='account_update'),
    url(r'^accounts/(?P<pk>\d+)/delete/$', views.AccountDelete.as_view(), name='account_delete'),
    url(r'^accounts/(?P<pk>\d+)/(?P<month>\S+)/$',
        views.AccountView.as_view(), name='account_detail'),
    url(r'^accounts/(?P<pk>\d+)/reconcile$',
        views.ReconcileView.as_view(), name='account_reconcile'),

    url(r'^accounts/new$', views.AccountCreate.as_view(), name='account_new'),

    url(r'^accounts$',
        views.AccountIndex.as_view(), name='personal_accounts'),

    url(r'^recurrences/$', views.RecurringTransactionIndex.as_view(), name='recurrences'),
    url(r'^recurrences/create$', views.RecurrenceCreateView.as_view(), name='recurrence_create'),
    url(r'^recurrences/(?P<pk>\d+)/update$', views.RecurrenceUpdateView.as_view(),
        name='recurrence_update'),
    url(r'^recurrences/(?P<pk>\d+)/delete$', views.RecurrenceDeleteView.as_view(),
        name='recurrence_delete'),
    url(r'^recurrences/(?P<pk>\d+)/skip$', api.skip_recurrence,
        name='recurrence_skip'),
    url(r'^recurrences/(?P<pk>\d+)/transaction/create$',
        views.RecurrenceTransactionCreateView.as_view(),
        name='recurrence_transaction_create'),


    url(r'^categories/$', views.CategoryIndex.as_view(), name='categories'),
    url(r'^categories/create/$', views.CategoryCreateView.as_view(), name='category_create'),
    url(r'^charts$', views.ChartView.as_view(), name='charts'),

    url(r'^api/accounts/(?P<account_type>\w+)$', api.get_accounts, name='api_accounts'),
    url(r'^api/accounts_balance/(?P<dstart>\S+)/(?P<dend>\S+)/$',
        api.get_accounts_balance, name='api_accounts_balance'),
    url(r'^manifest.json$', TemplateView.as_view(template_name='silverstrike/manifest.json'),
        name='manifest'),

    url(r'^import/$', views.ImportView.as_view(), name='import'),
    url(r'^import/firefly/$', views.ImportFireflyView.as_view(), name='import_firefly'),
    url(r'^import/generic$', views.ImportUploadView.as_view(), name='import_generic'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/$', views.ImportConfigureView.as_view(),
        name='import_configure'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/process/(?P<config_pk>\d+)/$',
        views.ImportProcessView.as_view(), name='import_process'),
]
