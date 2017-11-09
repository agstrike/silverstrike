from rest_framework import generics, serializers, viewsets, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from silverstrike.models import Account, Category, Transaction, Split


class ProtectSystemAccount(permissions.BasePermission):
    def has_object_permission(self, request, view, object):
        if request.method in permissions.SAFE_METHODS:
            return True
        return object.account_type != Account.SYSTEM


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'account_type', 'active', 'show_on_dashboard')

    def validate_account_type(self, value):
        if value == Account.SYSTEM:
            raise serializers.ValidationError("You can't create system accounts")
        return value


class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    splits = serializers.HyperlinkedIdentityField(many=True, read_only=True, view_name='split-detail')

    class Meta:
        model = Transaction
        fields = ('id', 'title', 'date', 'transaction_type', 'splits')

class AccountList(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (ProtectSystemAccount,)
    filter_fields = ('account_type',)

    @detail_route()
    def transactions(self, request, pk=None):
        account = self.get_object()
        transactions = Split.objects.filter(account=account)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = SplitSerializer(page, many=True, context={'request': request})
            return Response(serializer.data)
        serializer = SplitSerializer(transactions, many=True, context={'request': request})
        return Response(serializer.data)

class Transactions(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_fields = ('date', 'transaction_type')

class SplitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Split
        fields = ('id', 'title', 'date', 'account', 'opposing_account',
                  'amount', 'category', 'transaction')


class Splits(viewsets.ModelViewSet):
    queryset = Split.objects.all()
    serializer_class = SplitSerializer
    filter_fields = ('date', 'account', 'opposing_account', 'category', 'transaction__date', 'amount')


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class Categories(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
