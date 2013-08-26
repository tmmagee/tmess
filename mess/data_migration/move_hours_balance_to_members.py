'''
This very short script simply transfers all hours balances
from accounts to members. 

For each account with at least one active member the script transfers
the account's hour balance to the FIRST member on the account IF the 
account hours balance is not 0.

Why does an account hours balance have to be non-zero? Because Jane has 
already gone through many accounts and transferred many hours balance by 
hand. She then set the account hours balance for these accounts to 0. 
So account.hours_balance == 0 is a sign that Jane has already handled
the migration.
'''

import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))
import settings
from django.core.management import setup_environ
setup_environ(settings)

from mess.membership import models as m_models

for account in m_models.Account.objects.all():
  if account.active_member_count >= 1:
    
    member_hours_balance = 0
    top_active_member = account.active_members()[0]

    for member in account.active_members():
      member_hours_balance += member.hours_balance

    if account.hours_balance != 0 and member_hours_balance != account.hours_balance:
      top_active_member.hours_balance = account.hours_balance
      top_active_member.save()
      

