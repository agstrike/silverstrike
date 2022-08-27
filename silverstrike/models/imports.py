
import uuid

from django.db import models

from .account import Account


class ImportFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='imports')
    created_at = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, models.SET_NULL, null=True)
    importer = models.PositiveIntegerField(null=True)
