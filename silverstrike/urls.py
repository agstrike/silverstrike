from django.conf.urls import include, url
from django.views.generic import TemplateView


from silverstrike import api
from silverstrike.views import account as account_views
from silverstrike.views import budgets as budget_views
from silverstrike.views import categories as category_views
from silverstrike.views import charts as chart_views
from silverstrike.views import imports as import_views
from silverstrike.views import index as general_views
from silverstrike.views import recurrences as recurrence_views
from silverstrike.views import transactions as transaction_views


urlpatterns = [
    url(r'^$', general_views.IndexView.as_view(), name='index'),
    url(r'^auth/', include('allauth.urls')),

    url(r'^transactions/$', transaction_views.TransactionIndex.as_view(), name='transactions'),
    url(r'^transactions/(?P<pk>\d+)/$',
        transaction_views.TransactionDetailView.as_view(), name='transaction_detail'),
    url(r'^transactions/(?P<pk>\d+)/update/$',
        transaction_views.TransactionUpdateView.as_view(), name='transaction_update'),
    url(r'^transactions/(?P<pk>\d+)/split/$',
        transaction_views.SplitUpdate.as_view(), name='split_update'),
    url(r'^transactions/(?P<pk>\d+)/delete/$',
        transaction_views.TransactionDeleteView.as_view(), name='transaction_delete'),
    url(r'^transactions/create/transfer/$',
        transaction_views.TransferCreate.as_view(), name='transfer_new'),
    url(r'^transactions/create/withdraw/$',
        transaction_views.WithdrawCreate.as_view(), name='withdraw_new'),
    url(r'^transactions/create/deposit/$',
        transaction_views.DepositCreate.as_view(), name='deposit_new'),
    url(r'^transactions/create/split/$',
        transaction_views.SplitCreate.as_view(), name='split_create'),

    url(r'^accounts/(?P<pk>\d+)/update/$',
        account_views.AccountUpdate.as_view(), name='account_update'),
    url(r'^accounts/(?P<pk>\d+)/delete/$',
        account_views.AccountDelete.as_view(), name='account_delete'),
    url(r'^accounts/(?P<pk>\d+)/(?P<month>\S+)/$',
        account_views.AccountView.as_view(), name='account_detail'),
    url(r'^accounts/(?P<pk>\d+)/$', account_views.AccountView.as_view(), name='account_view'),
    url(r'^accounts/(?P<pk>\d+)/reconcile$',
        account_views.ReconcileView.as_view(), name='account_reconcile'),

    url(r'^accounts/new$', account_views.AccountCreate.as_view(), name='account_new'),

    url(r'^accounts$',
        account_views.AccountIndex.as_view(), name='accounts'),

    url(r'^recurrences/$',
        recurrence_views.RecurringTransactionIndex.as_view(), name='recurrences'),
    url(r'^recurrences/create$',
        recurrence_views.RecurrenceCreateView.as_view(), name='recurrence_create'),
    url(r'^recurrences/(?P<pk>\d+)/$', recurrence_views.RecurrenceDetailView.as_view(),
        name='recurrence_detail'),
    url(r'^recurrences/(?P<pk>\d+)/update$', recurrence_views.RecurrenceUpdateView.as_view(),
        name='recurrence_update'),
    url(r'^recurrences/(?P<pk>\d+)/delete$', recurrence_views.RecurrenceDeleteView.as_view(),
        name='recurrence_delete'),
    url(r'^recurrences/(?P<pk>\d+)/transaction/create$',
        recurrence_views.RecurrenceTransactionCreateView.as_view(),
        name='recurrence_transaction_create'),


    url(r'^categories/$', category_views.CategoryIndex.as_view(), name='categories'),
    url(r'^categories/month/(?P<month>\d+)/$', category_views.CategoryIndex.as_view(),
        name='categories_month'),
    url(r'^categories/create/$',
        category_views.CategoryCreateView.as_view(), name='category_create'),
    url(r'^categories/(?P<pk>\d+)/$',
        category_views.CategoryDetailView.as_view(), name='category_detail'),
    url(r'^categories/(?P<pk>\d+)/(?P<month>\S+)/$',
        category_views.CategoryDetailView.as_view(), name='category_month'),
    url(r'^categories/(?P<pk>\d+)/delete$', category_views.CategoryDeleteView.as_view(),
        name='category_delete'),
    url(r'^categories/(?P<pk>\d+)/update$', category_views.CategoryUpdateView.as_view(),
        name='category_update'),

    url(r'^budgets/$', budget_views.BudgetIndex.as_view(), name='budgets'),
    url(r'^budgets/(?P<month>\S+)/$', budget_views.BudgetIndex.as_view(), name='budget_month'),

    url(r'^charts$', chart_views.ChartView.as_view(), name='charts'),

    url(r'^api/accounts/(?P<account_type>\w+)$', api.get_accounts, name='api_accounts'),
    url(r'^api/balance/(?P<dstart>\S+)/(?P<dend>\S+)/$',
        api.get_balances, name='api_balance'),
    url(r'^api/accounts_balance/(?P<dstart>\S+)/(?P<dend>\S+)/$',
        api.get_accounts_balance, name='api_accounts_balance'),
    url(r'^api/category_spending/(?P<dstart>\S+)/(?P<dend>\S+)/$',
        api.category_spending, name='category_spending'),

    url(r'^manifest.json$', TemplateView.as_view(template_name='silverstrike/manifest.json'),
        name='manifest'),

    url(r'^import/$', import_views.ImportView.as_view(), name='import'),
    url(r'^import/firefly/$', import_views.ImportFireflyView.as_view(), name='import_firefly'),
    url(r'^import/generic$', import_views.ImportUploadView.as_view(), name='import_generic'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/$', import_views.ImportConfigureView.as_view(),
        name='import_configure'),
    url(r'^import/generic/(?P<uuid>[0-9a-f-]+)/process/(?P<config_pk>\d+)/$',
        import_views.ImportProcessView.as_view(), name='import_process'),

    url(r'^export/$', import_views.ExportView.as_view(), name='export'),
]
