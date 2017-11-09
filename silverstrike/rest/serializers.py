from rest_framework import generics, serializers, viewsets, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from silverstrike.models import Account, Category, Transaction, Split



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


class SplitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Split
        fields = ('id', 'title', 'date', 'account', 'opposing_account',
                  'amount', 'category', 'transaction')

class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
