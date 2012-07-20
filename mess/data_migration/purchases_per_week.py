import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))
import settings
from django.core.management import setup_environ
setup_environ(settings)
import datetime
STARTDATE = datetime.date(2009,9,20)
ENDDATE = datetime.date.today()

# these imports raise errors if placed before setup_environ(settings)
from mess.membership import models as m_models
from mess.accounting import models as a_models
import random
from decimal import Decimal

print '''This script counts the transactions of type 'Purchase' for each week.
 Transactions of other types (bulk, after-hours, etc) are not counted.'''

def main():
    oneweek = datetime.timedelta(days=7)    
    p = a_models.Transaction.objects.filter(purchase_type='P')
    s = STARTDATE
    while s < ENDDATE:
        print 'Starting %s:'% s ,
        print p.filter(timestamp__gte=s, timestamp__lt=s+oneweek).count()
        s += oneweek
                
if __name__=='__main__':
    main()
