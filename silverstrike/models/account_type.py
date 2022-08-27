from django.db import models
from django.utils.translation import gettext as _


class AccountType(models.IntegerChoices):
    PERSONAL = 1, _('Personal')
    FOREIGN = 2, _('Foreign')
    SYSTEM = 3, _('System')
