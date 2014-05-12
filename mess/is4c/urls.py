from django.conf.urls.defaults import *

urlpatterns = patterns('mess.is4c.views',
    url(r'^$', 'index', name='is4c-index'),
    url(r'^account/(\d+)/$', 'account', name='is4c-account'),
    url(r'^accounts/$', 'accounts', name='is4c-accounts'),
    url(r'^member/(\d+)/$', 'member', name='is5c-member'),
    url(r'^members/$', 'members', name='is4c-members'),
    url(r'^recordtransaction/$', 'recordtransaction', name='is4c-recordtransaction'),
    url(r'^gotois4c$', 'gotois4c', name='is4c-login'),
    url(r'^members_by_group/$', 'members_by_group', name='staff'),
    url(r'^groups/$', 'groups', name='groups'),
    url(r'^is4c_transaction_details/$', 'is4c_transaction_details', name='is4c-transactions-details'),
)
