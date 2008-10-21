from datetime import date

from django.db import models
from django.contrib.auth.models import User

MEMBER_STATUS = (
    ('a', 'Active'),
    ('L', 'Leave of Absence'),
    ('q', 'Quit'),
    ('m', 'Missing'),  # Member has disappeared without notice.
    ('i', 'Inactive'),
)
WORK_STATUS = (
    ('e','Excused'),
    ('w', 'Working'),  # Member is active and has a job.
    ('n', 'Non-Working'),  # Such as a single parent.
)
CONTACT_PREF = (
    ('e', 'Email'),
    ('t', 'Telephone'),
)

class Member(models.Model):
    user = models.ForeignKey(User, unique=True, editable=False)
    status = models.CharField(max_length=1, choices=MEMBER_STATUS,
                            default='a')
    work_status = models.CharField(max_length=1, choices=WORK_STATUS,
                            default='w')
    has_key = models.BooleanField(default=False)
    primary_account = models.ForeignKey('Account', blank=True, null=True)
    date_joined = models.DateField(default=date(1990, 01, 01))
    # leave contact_preference out -- simply email if provided
    #contact_preference = models.CharField(max_length=1, 
    #        choices=CONTACT_PREF, default='e')

    def __unicode__(self):
        return self.user.get_full_name()

    class Meta:
        ordering = ['user']

class Account(models.Model):
    name = models.CharField(max_length=50, unique=True)
    contact = models.ForeignKey(Member, related_name='contact_for')
    members = models.ManyToManyField(Member, related_name='accounts',)
    can_shop = models.BooleanField(default=True)

    # Do we want to keep an account balance here?  It would mean some
    # replication of data because balance can be found by tracing 
    # transactions, but it might be nice to have here for easier lookups.
    # An account's balance would have to be updated with each related 
    # transaction.save().
    # Also, people really shouldn't have null balances.  Even if it's a 
    # new account, a deposit should have been made.
    balance = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

