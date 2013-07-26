from os.path import dirname, abspath
import sys
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import settings
from django.core.management import setup_environ
setup_environ(settings)

from mess.membership import models as m_models
from mess.revision import models as r_models

for member in m_models.Member.objects.all():
  r_models.MemberRevision.create_member_revision(member)


for account in m_models.Account.objects.all():
  r_models.AccountRevision.create_account_revision(account)
