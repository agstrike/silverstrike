from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework import routers

from silverstrike import api
from silverstrike.rest import views as rest_views
from silverstrike.views import accounts as account_views
from silverstrike.views import budgets as budget_views
from silverstrike.views import categories as category_views
from silverstrike.views import charts as chart_views
from silverstrike.views import imports as import_views
from silverstrike.views import index as general_views
from silverstrike.views import recurrences as recurrence_views
from silverstrike.views import transactions as transaction_views


router = routers.DefaultRouter()
router.register(r'accounts', rest_views.AccountViewSet)
router.register(r'transactions', rest_views.TransactionViewSet)
router.register(r'categories', rest_views.CategoryViewSet)
router.register(r'recurrences', rest_views.RecurringTransactionsViewset)

urlpatterns = [
    path('', general_views.IndexView.as_view(), name='index'),
    path('profile/', general_views.ProfileView.as_view(), name='profile'),

    path('auth/', include('allauth.urls')),

    path('transactions/', transaction_views.TransactionIndex.as_view(), name='transactions'),
    path('transactions/<int:pk>/',
         transaction_views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/update/',
         transaction_views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/split/',
         transaction_views.SplitUpdate.as_view(), name='split_update'),
    path('transactions/<int:pk>/delete/',
         transaction_views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('transactions/create/transfer/',
         transaction_views.TransactionCreate.as_view(), {'type': 'transfer'}, name='transfer_new'),
    path('transactions/create/withdraw/',
         transaction_views.TransactionCreate.as_view(), {'type': 'withdraw'}, name='withdraw_new'),
    path('transactions/create/deposit/',
         transaction_views.TransactionCreate.as_view(), {'type': 'deposit'}, name='deposit_new'),
    path('transactions/create/split/',
         transaction_views.SplitCreate.as_view(), name='split_create'),

    path('accounts/<int:pk>/update/',
         account_views.AccountUpdate.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/',
         account_views.AccountDelete.as_view(), name='account_delete'),
    path('accounts/<int:pk>/all',
         account_views.AccountView.as_view(), {'period': 'all'}, name='account_detail_all'),
    path('accounts/<int:pk>/<dstart>/<dend>/',
         account_views.AccountView.as_view(), {'period': 'custom'}, name='account_detail'),
    path('accounts/<int:pk>/', account_views.AccountView.as_view(), {'period': 'month'},
         name='account_view'),
    path('accounts/<int:pk>/reconcile/',
         account_views.ReconcileView.as_view(), name='account_reconcile'),
    path('accounts/foreign/',
         account_views.ForeignAccountIndex.as_view(), name='foreign_accounts'),
    path('accounts/foreign/create/',
         account_views.ForeignAccountCreate.as_view(), name='foreign_account_new'),
    path('accounts/new/', account_views.AccountCreate.as_view(), name='account_new'),
    path('accounts/', account_views.AccountIndex.as_view(), name='accounts'),

    path('recurrences/',
         recurrence_views.RecurringTransactionIndex.as_view(), name='recurrences'),
    path('recurrences/create/',
         recurrence_views.RecurrenceCreateView.as_view(), name='recurrence_create'),
    path('recurrences/disabled/',
         recurrence_views.DisabledRecurrencesView.as_view(), name='disabled_recurrences'),
    path('recurrences/<int:pk>/', recurrence_views.RecurrenceDetailView.as_view(),
         name='recurrence_detail'),
    path('recurrences/<int:pk>/update/', recurrence_views.RecurrenceUpdateView.as_view(),
         name='recurrence_update'),
    path('recurrences/<int:pk>/delete/', recurrence_views.RecurrenceDeleteView.as_view(),
         name='recurrence_delete'),
    path('recurrences/<int:pk>/transaction/create/',
         recurrence_views.RecurrenceTransactionCreateView.as_view(),
         name='recurrence_transaction_create'),


    path('categories/', category_views.CategoryIndex.as_view(), name='categories'),
    path('categories/inactive/', category_views.InactiveCategoriesView.as_view(),
         name='inactive_categories'),
    path('categories/month/<int:year>/<int:month>/', category_views.CategoryIndex.as_view(),
         name='categories_month'),
    path('categories/assign/',
         category_views.assign_categories, name='category_assign'),
    path('categories/create/',
         category_views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/',
         category_views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/<int:year>/<int:month>/',
         category_views.CategoryDetailView.as_view(), name='category_month'),
    path('categories/<int:pk>/delete/', category_views.CategoryDeleteView.as_view(),
         name='category_delete'),
    path('categories/<int:pk>/update/', category_views.CategoryUpdateView.as_view(),
         name='category_update'),

    path('budgets/', budget_views.BudgetIndex.as_view(), name='budgets'),
    path('budgets/<int:year>/<int:month>/',
         budget_views.BudgetIndex.as_view(), name='budget_month'),

    path('charts/', chart_views.ChartView.as_view(), name='charts'),

    path('api/accounts/<account_type>/', api.get_accounts, name='api_accounts'),
    path('api/balance/<dstart>/<dend>/', api.get_balances, name='api_balance'),
    path('api/account/<int:account_id>/balance/<dstart>/<dend>/',
         api.get_account_balance, name='api_account_balance'),
    path('api/accounts_balance/<dstart>/<dend>/',
         api.get_accounts_balance, name='api_accounts_balance'),
    path('api/category_spending/<dstart>/<dend>/',
         api.category_spending, name='category_spending'),

    path('manifest.json', TemplateView.as_view(template_name='silverstrike/manifest.json'),
         name='manifest'),

    path('import/', import_views.ImportView.as_view(), name='import'),
    path('import/firefly/', import_views.ImportFireflyView.as_view(), name='import_firefly'),
    path('import/generic/', import_views.ImportUploadView.as_view(), name='import_generic'),
    path('import/generic/<uuid:uuid>/', import_views.ImportConfigureView.as_view(),
         name='import_configure'),
    path('import/generic/<uuid:uuid>/process/<int:config_pk>/',
         import_views.ImportProcessView.as_view(), name='import_process'),

    path('export/', import_views.ExportView.as_view(), name='export'),

    path('rest/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

]
