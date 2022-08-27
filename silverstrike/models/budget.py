
from django.db import models

from .category import Category


class BudgetQuerySet(models.QuerySet):
    def for_month(self, month):
        return self.filter(month=month)


class Budget(models.Model):
    category = models.ForeignKey(Category, models.CASCADE)
    month = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BudgetQuerySet.as_manager()
