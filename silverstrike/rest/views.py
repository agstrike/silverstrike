from rest_framework import views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from silverstrike.models import (Account, AccountType, Category,
                                 RecurringTransaction, Split, Transaction)
from silverstrike.rest import serializers
from silverstrike.rest.permissions import ProtectSystemAccount
from silverstrike.rest.serializers import (AccountSerializer, CategorySerializer,
                                           RecurringTransactionSerializer,
                                           SplitSerializer, TransactionSerializer)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (ProtectSystemAccount,)

    @action(detail=True)
    def transactions(self, request, pk=None):
        account = self.get_object()
        transactions = Split.objects.filter(account=account)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = SplitSerializer(page, many=True, context={'request': request})
            return Response(serializer.data)
        serializer = SplitSerializer(transactions, many=True, context={'request': request})
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class RecurringTransactionsViewset(viewsets.ModelViewSet):
    queryset = RecurringTransaction.objects.all()
    serializer_class = RecurringTransactionSerializer


class AccountNameView(views.APIView):
    def get(self, request, format=None):
        serializer = serializers.AccountNameSerializer(Account.objects.all(), many=True)
        return Response(serializer.data)


class RecurrenceNameView(views.APIView):
    def get(self, request, format=None):
        serializer = serializers.RecurrenceNameSerializer(
            RecurringTransaction.objects.all(), many=True)
        return Response(serializer.data)


class PersonalAccountsView(views.APIView):
    def get(self, request, format=None):
        serializer = serializers.AccountSerializer(
            Account.objects.filter(account_type=AccountType.PERSONAL), many=True)
        return Response(serializer.data)


class ForeignAccountsView(views.APIView):
    def get(self, request, format=None):
        serializer = serializers.AccountSerializer(
            Account.objects.filter(account_type=AccountType.FOREIGN), many=True)
        return Response(serializer.data)
