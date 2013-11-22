"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import datetime
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from mess.membership import models

class AccountTests(TestCase):

  def create_member(self, name):
    user = User.objects.create(username=name)
    member = models.Member.objects.create(user=user)

    return member

  def create_account(self, name):
    account = models.Account.objects.create(
        name=name,
        ebt_only = False,
        note="",
        )

    return account

  def create_account_member(self, account, member):
    account_member = models.AccountMember.objects.create(
          account=account, 
          member=member,
          )

    return account_member

  def test_create_member(self):
    member = self.create_member("Test Member")

    self.assertTrue(type(member) is models.Member)

  def test_create_account(self):
    account = self.create_account("Test Member")

    self.assertTrue(type(account) is models.Account)

  def test_balance_limit(self):

    account = self.create_account("Test Account")
    members = []

    # Create three members
    for i in range(3):
      member = self.create_member("Test Member " + str(i))
      members.append(member)
      self.create_account_member(account, member)

    # Max allowed balance should be 3 * 5
    self.assertEqual(
        account.max_allowed_balance, 
        Decimal(3) * Decimal(5)
        )

    # Now set date joined to be six months in the past
    members[0].date_joined = datetime.datetime.today() - datetime.timedelta(180)
    members[0].save()

    # Max allowed balance should be 3 * 25
    self.assertEqual(
        account.max_allowed_balance, 
        Decimal(3) * Decimal(25)
        )

