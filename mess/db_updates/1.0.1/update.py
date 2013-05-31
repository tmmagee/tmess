from mess.membership import models

'''
For this update we are grandfathering in old balance limits to 
our new system for recording the balance limit (which is just
a field in the Accounts table now).

In the old system the balance limit was calculated by the 
number of people and the account and the length of time 
people were members. If ONE member had been a member for
at least 6 months (or 180 days), then the balance limit 
was $25*(number of active people on account). Less than
six months and it was $5*(number of active people on account)
'''
for account in models.Account.objects.all():
  if account.days_old() >= 180:
    account.balance_limit=25.00*account.active_member_count
    account.save()
  else:
    account.balance_limit=5.00*account.active_member_count
    account.save()

