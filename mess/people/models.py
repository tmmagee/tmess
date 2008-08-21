from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import permalink
from django.contrib.auth.models import User

from mess.contact.models import Address, Phone, Email

class Person(models.Model):
    """
    """
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, unique=True)
    addresses = models.ManyToManyField(Address, blank=True, null=True)
    phones = models.ManyToManyField(Phone, blank=True, null=True)
    emails = models.ManyToManyField(Email, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Admin:
        pass
