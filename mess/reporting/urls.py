from django.conf.urls.defaults import *

urlpatterns = patterns('mess.reporting.views',
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^list/$', 'list', name='list'),
    url(r'^equity/$', 'equity', name='equity'),
    url(r'^equity_by_member', 'equity_by_member', name='equity_by_member'),
    url(r'^equity_transfer/$', 'equity_transfer', name='equity_transfer'),
    url(r'^equity_old/$', 'equity_old', name='equity_old'),
    url(r'^anomalies/$', 'anomalies', name='anomalies'),
    url(r'^memberwork/$', 'memberwork', name='memberwork'),
    url(r'^trans_summary/$', 'trans_summary', name='trans_summary'),
    url(r'^hours_balance_changes/account/$', 'account_hours_balance_changes', name='account_hours_balance_changes'),
    url(r'^hours_balance_changes/member/$', 'member_hours_balance_changes', name='member_hours_balance_changes'),
    url(r'^turnout/$', 'turnout', name='turnout'),
    url(r'^logging/(\w+)/$', 'logging', name='logging'),
    url(r'^historical/members/$', 'historical_members', name='historical_members'),
    url(r'^hours_balance_migration_status/$', 'hours_balance_migration_status', name='hours_balance_migration_status'),
    url(r'^staff_account_balances/$', 'staff_account_balances', name='staff_account_balances'),

    # everything below here is partly unused or deprecated
    #url(r'^trans_list/$', 'transaction_list_report', name='trans_list'),
)
