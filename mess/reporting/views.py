from datetime import date, timedelta
import datetime
import time

# list is a function in this module, so to call the __builtin__.list function
# we have to import the namespace
import __builtin__ 

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Template, Context
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.aggregates import Sum, Max

from mess.accounting import models as a_models
from mess.accounting.models import Transaction
from mess.membership import models as m_models
from mess.scheduling import models as s_models
from mess.scheduling.views import old_rotations
#from mess.accounting.models import get_credit_choices, get_debit_choices
#from mess.accounting.models import get_trans_total
from mess.reporting import forms

from mess.utils.search import list_usernames_from_fullname

today = datetime.date.today()

def find_dups(mems):
    uniqs = {}
    dups = []
    found_dups = {}
    for member in mems:
        fullname = member.user.get_full_name()
        if fullname in uniqs:
            dups.append(member)
            if fullname not in found_dups:
                dups.append(uniqs[fullname])
                found_dups[fullname] = 1
        else:
            uniqs[fullname] = member
    return dups

def anomalies(request):
    blips = 0
    report = ''
    mems = m_models.Member.objects.all()
    issues = [
        ('Missing Firstname', mems.filter(user__first_name='Firstname')),
        ('Semicolon in Name', mems.filter(user__first_name__contains=';')),
        ('Comma in Name', mems.filter(user__first_name__contains=',')),
        ('Missing Lastname', mems.filter(user__last_name='Lastname')),
        ('Duplicate Name', find_dups(mems)),
        ('Email without @', mems.filter(user__email__isnull=False).exclude(user__email__contains='@')),
        ]
    for issue, afflicteds in issues:
        report += '<h3>%s (%d members)</h3>\n' % (issue, len(afflicteds))
        blips += len(afflicteds)
        for m in afflicteds:
            report += '<a href="/membership/members/%s">%s</a> \
                (<a href="/membership/accounts/%s">%s</a>)<br>\n' % \
                (m.user.username, m, m.get_primary_account().id, m.get_primary_account())

    report = '<h1>Anomalies Report (%d blips)</h1>\n' % blips + report
    return HttpResponse(report)

def reports(request):
    # each named category can have various reports, each with a name and url
    past90d = datetime.date.today() - datetime.timedelta(90)
    report_categories = [{'name':cat_name, 'reports':
            [{'name':rpt_name, 'url':url} for rpt_name, url in cat_rpts] 
            } for cat_name, cat_rpts in [

        ('Accounts',[
            listrpt('Accounts','Active Contacts',
                '',
                '{% for y in x.accountmember_set.all %}{% if y.member.is_active %}{{ y.member }}{% if y.account_contact %}*{% endif %}{% if y.shopper %}(s){% endif %}<br>{% endif %}{% endfor %}\*=Member Equity, (s)=Shopper\r\n'+
                '{% for y in x.members.active %}{% for z in y.phones.all %}{{ y.user.first_name }}: {{ z }}<br>{% endfor %}{% endfor %}\Phones\r\n'+
                '{% for y in x.members.active %}{% if y.user.email %}{{ y.user.first_name }}: {{ y.user.email }}<br>{% endif %}{% endfor %}\Emails\r\n'+
                'deposit'),

#           listrpt('Accounts','Active Addresses',
#               '',
#               '{% for y in x.accountmember_set.all %}{% if y.member.is_active %}{{ y.member }}{% if y.account_contact %}*{% endif %}{% if y.shopper %}(s){% endif %}<br>{% endif %}{% endfor %}\*=Member Equity, (s)=Shopper\r\n'+
#               '{% for y in x.members.active %}{% for z in y.addresses.all %}{% if not forloop.parentloop.first %}<br><br>{% endif %}{{ z.fullmailing|linebreaksbr }}<br>{% endfor %}{% endfor %}\Addresses'),
                
# broken :(
#           listrpt('Accounts','Needing Shifts? Incomplete List',
#               'task__time__gte!='+str(datetime.date.today())+'\r\nmembers__work_status__in!=ecn',
#               'note'),

# this duplicates all multi-member accounts :(
#           listrpt('Accounts','With A Member On LOA',
#               'members__leaveofabsence__start__lte='+str(datetime.date.today())+'\r\nmembers__leaveofabsence__end__gte='+str(datetime.date.today()),
#               '{% for m in x.members.all %}{% for l in m.leaveofabsence_set.all %}{{ m }}: LOA {{ l.start }} until {{ l.end }}<br>{% endfor %}{% endfor %}\\Members\r\nnote',
#               order_by='members__leaveofabsence__end'),

            listrpt('Accounts','With No Proxy Shoppers',
                'accountmember__shopper!=True', 'members\r\nactive_member_count'),

            listrpt('Accounts','With At Least $50 Member Equity',
                'deposit__gte=50.00', 'deposit'),

            ('Hours Balance Changes',reverse('hours_balance_changes')),            

            listrpt('Accounts','Owing 1 Hour or More',
                'hours_balance__gte=1.00', 
                'hours_balance\r\nbalance\r\n'+
                '{% for y in x.members.active %}{% for z in y.phones.all %}{{ y.user.first_name }}: {{ z }}<br>{% endfor %}{% endfor %}\Phones\r\n'+
                '{% for y in x.members.active %}{% if y.user.email %}{{ y.user.first_name }}: {{ y.user.email }}<br>{% endif %}{% endfor %}\Emails\r\n'+
                'billable_member_count\r\nnote',
                order_by='-hours_balance',
                include='Present'),

            listrpt('Accounts','Over Balance',
                'balance__gte=25',
                'balance\r\nmax_allowed_balance\r\nhours_balance\r\n'+
                '{% for y in x.members.active %}{% for z in y.phones.all %}{{ y.user.first_name }}: {{ z }}<br>{% endfor %}{% endfor %}\Phones\r\n'+
                '{% for y in x.members.active %}{% if y.user.email %}{{ y.user.first_name }}: {{ y.user.email }}<br>{% endif %}{% endfor %}\Emails\r\n'+
                'active_member_count\r\nnote',
                order_by='-balance',
                include='Present'),

            ('Keys to Shut Off',reverse('frozen')+'?has_key=on'),

        ]),

        ('Members',[

            listrpt('Members','Active Addresses',
                'accountmember__shopper=False',
                'accounts\r\n'+
                '{% with x.addresses.all|first as z %}{{ z.address1 }}{% endwith %}\Street1\r\n'+ 
                '{% with x.addresses.all|first as z %}{{ z.address2 }}{% endwith %}\Street2\r\n'+ 
                '{% with x.addresses.all|first as z %}{{ z.city }}{% endwith %}\City\r\n'+
                '{% with x.addresses.all|first as z %}{{ z.state }}{% endwith %}\State\r\n'+
                '{% with x.addresses.all|first as z %}{{ z.postal_code }}{% endwith %}\ZIP\r\n'+
                '{% with x.addresses.all|first as z %}{{ z.country }}{% endwith %}\Country\r\n'+
                '{% ifnotequal x.addresses.count 0 %}{% ifnotequal x.addresses.count 1 %}*another address on record*{% endifnotequal %}{% endifnotequal %}\Other Addresses',
                order_by='accounts'),

            listrpt('Members','by Last Name',
                'accountmember__shopper=False',
                'user.last_name\r\n'+
                'user.first_name\r\n'+
                'accounts\r\n'+
                'date_joined\r\n'+
                'phones\r\n'+
                'user.email\r\n'+
                '{% with x.addresses.all|first as z %}{{ z.address1 }}{% endwith %}\Street1\r\n'+ 
                '{% with x.addresses.all|first as z %}{{ z.address2 }}{% endwith %}\Street2\r\n'+ 
                '{% with x.addresses.all|first as z %}{{ z.postal_code }}{% endwith %}\ZIP\r\n'+
                '{% with x.accounts.all|first as z %}{{ z.deposit }}{% endwith %}\Deposit',
                order_by='user__last_name'),

            listrpt('Members','with Email',
                'user__email!=', 'accounts\r\nuser.email\r\nBox:user.email',
                order_by='accounts'),

            listrpt('Members','without Email (phone list)',
                'user__email=\r\naccountmember__shopper=False',
                'accounts\r\nphones', order_by='accounts'),

            listrpt('Members','Member Equity Holders on LOA',
                'leaveofabsence__start__lte='+str(datetime.date.today())+'\r\nleaveofabsence__end__gte='+str(datetime.date.today())+'\r\naccountmember__shopper=False',
                'current_loa.start\r\ncurrent_loa.end\r\naccounts\r\nphones\r\n{% for a in x.accounts.all %}{{ a.note }}{% endfor %}\Notes',
                order_by='leaveofabsence__end'),

            listrpt('Members','On LOA',
                'leaveofabsence__start__lte='+str(datetime.date.today())+'\r\nleaveofabsence__end__gte='+str(datetime.date.today()),
                'current_loa.start\r\ncurrent_loa.end\r\naccounts\r\nphones\r\n{% for a in x.accounts.all %}{{ a.note }}{% endfor %}\Notes',
                order_by='leaveofabsence__end'),

            listrpt('Members','Back from LOA',
                'leaveofabsence__end__lte='+str(datetime.date.today())+'\r\nleaveofabsence__end__gte='+str(datetime.date.today()-datetime.timedelta(30)),
                '{% for l in x.leaveofabsence_set.all %}{{ l.end }}{% endfor %}\Return Date\r\naccounts\r\nphones\r\n{% for a in x.accounts.all %}{{ a.note }}{% endfor %}\Notes',
                order_by='-leaveofabsence__end'),

            listrpt('Members','New',# since '+past90d.strftime('%B %e, %Y'),
                'date_joined__gte='+str(past90d), 
                'accounts\r\ndate_joined\r\ndate_orientation',
                order_by='-date_joined'),

            listrpt('Members','Recently Departed',# (since '+past90d.strftime('%B %e, %Y')+')',
                'date_departed__gte='+str(past90d), 
                'accounts\r\ndate_joined\r\ndate_departed',
                order_by='-date_departed',
                include='All'),

            listrpt('Members','Keycard Info',
                'card_number__gt=',
                'accounts\r\ncard_number\r\ncard_facility_code\r\ncard_type',
                order_by='accounts'),
        ]),

        ('Accounting',[
            ('Cash Sheets',reverse('cashsheet')),

            ('Transaction Summary',reverse('trans_summary')),

            listrpt('Accounts','Purchases Per Account Last 7 Days',
                '','TSum:0:7:P\r\nTSum:0:7:B\r\nTSum:0:7:A'),

            listrpt('Accounts','All Balances and Member Equities',
                '','balance\r\ndeposit\r\nactive_member_count',
                include='All'),

#           listrpt('Accounts','Active+Missing Balances and Member Equities',
#               'members__isnull=False\r\n'+
#               'members__date_departed__isnull=True',
#               'balance\r\ndeposit\r\nactive_member_count\r\n'+
#               'active_or_missing_count',
#               include_inactive='on'),

            listrpt('Accounts','Active Balances and Member Equities',
                '','balance\r\ndeposit\r\nactive_member_count'),

            ('Member Equities Billing (New 2011)',reverse('billing')),
            ('One-time Equity Transfer',reverse('equity_transfer')),
            ('Equity Totals',reverse('equity')),
        ]),

        ('Tasks',[
            ('Wall Calendar', reverse('scheduling-rotation')),

            listrpt('Tasks','Cashiers With Email',
                'job__name=Cashier\r\nmember__isnull=False',
                'job\r\nmember\r\naccount\r\nmember.user.email\r\nBox:member.user.email'),

            listrpt('Tasks','Storekeepers',
                'job__name=Store Keeper\r\nmember__isnull=False',
                'job\r\nmember\r\naccount'),

            listrpt('Tasks','Unfilled Next 7 Days',
                'member__isnull=True\r\nexcused=False\r\ntime__lte='+
                    str(datetime.date.today()+datetime.timedelta(days=7)),
                'job'),

            ('Workshift Turnout', reverse('turnout')),
        ]),

        ('Member Work',[
            ('Member Work Dashboard', reverse('memberwork')),
            ('Need Shift', reverse('memberwork')+'?section=Need Shift'),
            ('Regular Shift', reverse('memberwork')+'?section=Regular Shift'),
            ('Exemptions', reverse('memberwork')+'?section=Exempt'),
            ('Committee', reverse('memberwork')+'?section=Committee'),
            ('No Workshift', reverse('memberwork')+'?section=No Workshift'),
        ]),

        ('Anomalies',[
            ('Page For Fixing "Member Equity Holder" and "Shopper"',
                reverse('accountmemberflags')),
            ('Database Anomalies',reverse('anomalies')),
        ]),

        ('Old Reports',[
            ('Equity By Account (Old)',reverse('equity_old')),
            ('Dues and Member Equities Billing (Old)',reverse('billing_old')),

            listrpt('Accounts','Accounts With Permanent Shifts',
                'task__time__year='+str(datetime.date.today().year+1),
                '{% for m in x.members.all %}{{ m }}: {{ m.next_shift }}<br>{% endfor %}\\Shifts by Member\r\nnote'),

            listrpt('Accounts','Accounts With A Work Exemption',
                'members__work_status=e',
                '{% for m in x.members.all %}{{ m }}: {{ m.get_work_status_display }}<br>{% endfor %}\\Members\r\nnote'),

            listrpt('Accounts','Accounts With Committee Work',
                'members__work_status=c',
                '{% for m in x.members.all %}{{ m }}: {{ m.get_work_status_display }}<br>{% endfor %}\\Members\r\nnote'),

            listrpt('Accounts','Accounts With Non-Working Members',
                'members__work_status=n',
                '{% for m in x.members.all %}{{ m }}: {{ m.get_work_status_display }}<br>{% endfor %}\\Members\r\nnote'),

            listrpt('Accounts','Electors (use Active Contacts instead)',
                '',
                '{% for y in x.accountmember_set.all %}{{ y.member }}{% if y.account_contact and not y.member.date_departed and not y.member.date_missing %}*{% endif %}<br>{% endfor %}\\*=Elector\r\nactive_member_count\r\ndeposit'),

        ]),
        ('Logging', [
#            listrpt('Logs', 'General',
#                '',
#                'action_time\r\nuser\r\ncontent_type\r\nobject_id\r\nobject_repr\r\naction_flag\r\nchange_message'),
            ('Accounts',reverse('logging', args=['account'])),
            ('Members',reverse('logging', args=['member'])),
        ]),
#        ('Historical', [
##            listrpt('Logs', 'General',
##                '',
##                'action_time\r\nuser\r\ncontent_type\r\nobject_id\r\nobject_repr\r\naction_flag\r\nchange_message'),
#            ('Members By Date',reverse('historical_members')),
#        ]),
        ]]
    return render_to_response('reporting/reports.html', locals(),
            context_instance=RequestContext(request))

def listrpt(object, desc, filter, output, include='Active', order_by=''):
    return (desc, reverse('list')+'?'+urlencode(locals()))

def list(request):
    context = RequestContext(request)
    context['form'] = forms.ListFilterForm(request.GET)
    context['errors'] = []
    if request.GET.has_key('desc'):
        context['desc'] = request.GET['desc']

    for requestfield in ['object','include','filter','order_by','output']:
        if request.GET.has_key('object') and context['form'].is_valid():
            context[requestfield] = context['form'].cleaned_data[requestfield]
        else:
            context[requestfield] = ''
    
    if context['object'] == 'Accounts':
        if context['include'] == 'All':
            objects = m_models.Account.objects.all()
        elif context['include'] == 'Present':
            objects = m_models.Account.objects.present()
        else:  # default Active
            objects = m_models.Account.objects.active()
        blank_object = m_models.Account()
        outputters = [ListOutputter('', blank_object, 'Account')]
    elif context['object'] == 'Members':
        if context['include'] == 'All':
            objects = m_models.Member.objects.all()
        elif context['include'] == 'Present':
            objects = m_models.Member.objects.present()
        else:  # default Active
            objects = m_models.Member.objects.active()
        blank_object = m_models.Member()
        outputters = [ListOutputter('', blank_object, 'Member')]
    elif context['object'] == 'Tasks':
        objects = s_models.Task.objects.all()
        if context['include'] != 'All':
            # show only tasks in the next 6 weeks...
            objects = objects.filter(time__range=(datetime.date.today(),datetime.date.today()+datetime.timedelta(weeks=6)))
            # ...or in the next 4 weeks if we're sure it's a 4-week rotation
            objects = objects.exclude(time__gt=datetime.date.today()+datetime.timedelta(weeks=4), recur_rule__interval=4)
        blank_object = s_models.Task()
        outputters = [ListOutputter('<a href="{% url scheduling-task x.id %}">{{ x }}</a>', blank_object, 'Task')]
    elif context['object'] == 'Logs':
        objects = LogEntry.objects.all()
        blank_object = LogEntry()
        outputters = [ListOutputter('{{ x }}', blank_object, 'Log')]
    else:
        objects = [] 
        outputters = []

    for filterline in context['filter'].split('\r\n'):
        if len(filterline) == 0:
            continue
        try:
            filterq, filterval = filterline.split('=')
            if filterval == 'True': 
                filterval = True
            if filterval == 'False': 
                filterval = False
            if filterq[-1] == '!':
                objects = objects.exclude(**{str(filterq[:-1]):filterval})
            else:
                objects = objects.filter(**{str(filterq):filterval}).distinct()
        except:
            context['errors'].append(filterline)

    for order_by_line in context['order_by'].split('\r\n'):
        if len(order_by_line) == 0:
            continue
        try:
            objects = objects.order_by(order_by_line).distinct()
        except:
            context['errors'].append(order_by_line)

    for outfield in context['output'].split('\r\n'):
        if len(outfield) == 0:
            pass
        elif outfield[:4] == 'Box:':
            y = ListOutputter(outfield[4:], blank_object)
            context['textarea'] = [y.render(x).replace('<br>',',\r\n') 
                                   for x in objects]
        else:
            outputters.append(ListOutputter(outfield, blank_object))

    context['outputfieldnames'] = outputters
    if request.GET.has_key('export'):
        context['uri'] = request.build_absolute_uri()
        context['result'] = [[y.render(x, export=True) 
                              for y in outputters] for x in objects]
        template = get_template('reporting/listexport.tsv')
        context['totals'] = [y.total for y in outputters[1:]]
        resp = HttpResponse(template.render(context), mimetype='application/vnd.ms-excel')
        resp['Content-Disposition'] = 'attachment; filename=mess.tsv'
        return resp
    else:
        context['result'] = [[y.render(x) 
                              for y in outputters] for x in objects]
        template = get_template('reporting/list.html')
        context['totals'] = [y.total for y in outputters[1:]]
        return HttpResponse(template.render(context))

class ListOutputter:
    def __init__(self, field, blank_object, name=None):
        self.field = field
        self.total = 0
        self.name = name or field.title()
        if not field:
            self.fieldpath = []
            self.render = self.render_by_getattr
        elif '{' in field:
            self.render = self.render_as_template
            if '\\' in field:
                self.field, self.name = field.split('\\',1)
            self.template = Template(self.field)
        elif field[:5] == 'TSum:':
            daysago, daysprior, self.tsumtype = field[5:].split(':')
            self.daterange = (datetime.date.today()-datetime.timedelta(int(daysprior)),
                              datetime.date.today()-datetime.timedelta(int(daysago)))
            self.render = self.render_tsum            
            self.name = 'Sum of %s' % dict(a_models.PURCHASE_CHOICES)[self.tsumtype]
        else:
            self.fieldpath = self.field.split('.')
            self.render = self.render_by_getattr

    def render_tsum(self, object, export=False):
        ts = object.transaction_set.filter(timestamp__range=self.daterange,
            purchase_type=self.tsumtype).aggregate(Sum('purchase_amount')).values()[0]
        if ts:
            self.total += ts
        return ts

    def render_as_template(self, object, export=False):
        object_context = Context({'x':object})
        try:
            return self.template.render(object_context)
        except:
            return 'error: '+self.field
        
    def render_by_getattr(self, object, export=False):
        for pathpiece in self.fieldpath:
            if not hasattr(object, pathpiece):
                return 'error: '+self.field
            object = getattr(object, pathpiece)
        if hasattr(object, 'all'):
            if export:
                return u'; '.join([self._render_obj(relobj, export=True)
                                   for relobj in object.all()])
            else:
                return mark_safe(u'<br>'.join([self._render_obj(relobj) 
                                           for relobj in object.all()]))
        else:
            return self._render_obj(object, export=export)

    def _render_obj(self, object, export=False):
        if hasattr(object, 'get_absolute_url') and not export:
            # mark_safe  tells the template not to escape the <html tags>
            return mark_safe(u'<a href="%s">%s</a>' %(
                             object.get_absolute_url(), object))
        else:
            try:
                self.total += object
            except:
                pass
            return unicode(object)

    def __unicode__(self):
        return self.name

def memberwork(request):
    '''
    list of members, summarizing work status, grouped by work status
    '''
    cycle_begin = datetime.datetime(2009,1,26)
    weekbreaks = {}
    for freq in [4,6]:
        dayone = cycle_begin
        while dayone.date() < datetime.date.today():
            dayone += datetime.timedelta(days=7*freq)
        dayz = [dayone+datetime.timedelta(days=7*freq*i) 
                for i in range(-int(18/freq),1)]
        weekbreaks[freq] = [datetime.datetime.combine(x, datetime.time.min) 
                            for x in dayz]
    memberwork = []
    distinctmembers = {}
    proxypair = {}
    for member in m_models.Member.objects.active().order_by('accounts'):
        if member in distinctmembers: 
            continue
        distinctmembers[member] = True
        mw = prepmemberwork(member, weekbreaks)
        memberwork.append(mw)

        # If a proxy has a shift, and someone else in the account needs
        # a shift, match them up in a 'proxy shift pairs' section.
        # This way 'Need Shift' is only people who REALLY need a shift.
        if mw.section == 'Proxy' and mw.shift:
            proxypair[mw.get_primary_account()] = mw
    for mw in memberwork:
        if mw.section == 'Need Shift' and mw.get_primary_account() in proxypair:
            mw.section = 'Proxy Shift Pairs'
            proxypair[mw.get_primary_account()].section = 'Proxy Shift Pairs'

    section_names = ['Regular Shift', 'Cashiers', 'Dancers', 'Committee', 
        'Exempt', 'No Workshift', 'LOA', 'Need Shift', 'Proxy Shift Pairs', 
        'Proxy']
    if 'section' in request.GET:
        section_names = [request.GET['section']]
    sections = [{'name':x, 
                 'memberwork':[mw for mw in memberwork if mw.section == x]} 
               for x in section_names]
    return render_to_response('reporting/memberwork.html', locals(),
            context_instance=RequestContext(request))

def prepmemberwork(member, weekbreaks):
    # return this very member object, but just add things onto it.
    shift = member.regular_shift()
    if shift:
        shift.rotletter = old_rotations(shift.time, shift.recur_rule.interval)
    if shift and shift.recur_rule.interval == 6:
        freq = 6
    else:
        freq = 4
    member.shift = shift
    member.freq = freq
    member.cycletasks = [member.task_set.filter(time__range=(
            weekbreaks[freq][i], weekbreaks[freq][i+1])) 
            for i in range(len(weekbreaks[freq])-1)]
    if member.accountmember_set.filter(shopper=False).count() == 0:
        section = 'Proxy'
    elif member.is_on_loa:
        section = 'LOA'
    elif member.work_status == 'e':
        section = 'Exempt'
    elif member.work_status == 'c':
        section = 'Committee'
    elif member.work_status == 'n':
        section = 'No Workshift'
    elif member.shift == None:
        section = 'Need Shift'
    elif member.shift.job.name == 'Cashier':
        section = 'Cashiers'
    elif 'Dancer' in member.shift.job.name:
        section = 'Dancers'
    else:
        section = 'Regular Shift'
    member.section = section
    return member


def transaction_list_report(request):
    # c is the context to be passed to the template
    c = RequestContext(request)
    c['page_name'] = 'Transaction List'
    c['report_title'] = 'List of Transactions Matching Filter'

    # start with all transactions
    trans = Transaction.objects

    # if account or member specified, filter that
    if request.GET.has_key('account'): 
        c['account']=request.GET.get('account')
        if c['account'] != "":
            trans = trans.filter(account__name = c['account'])
    if request.GET.has_key('member'):
        c['member'] = request.GET.get('member')
        if c['member'] != "":
            c['usernames'] = list_usernames_from_fullname(c['member'])
            trans = trans.filter(member__user__username__in = c['usernames'])

    # Filter date range -- default to 1900-today.
    # If query date is invalid, error is ugly.  But that shouldn't happen.
    # strptime is hard to use, so here I do yyyy-mm-dd2date as slices.
    # End would be midnight before, but we want midnight after, so timedelta.
    if request.GET.has_key('start'):
        ymd = request.GET.get('start')
        c['start'] = date(int(ymd[:4]),int(ymd[5:7]),int(ymd[8:]))
    else: c['start'] = date(1900,1,1)
    if request.GET.has_key('end'): 
        ymd = request.GET.get('end')
        c['end'] = date(int(ymd[:4]),int(ymd[5:7]),int(ymd[8:]))
    else: c['end'] = date.today()
    if c['end'] < c['start']: (c['start'],c['end']) = (c['end'],c['start'])
    trans = trans.filter(date__range=(c['start'], c['end']+timedelta(days=1)))

    c['transactions'] = trans
    return render_to_response('reporting/transactions_list.html', c)

def hours_balance_changes(request):
    """
    View to summarize hours transactions in a given time period

    Paul says, "This function is better now."  See form.full_clean
    It accepts any combo of provided fields, eg, account with no dates.
    """
    form = forms.HoursBalanceChangesFilterForm(request.GET)
    if form.is_valid():    # empty form is valid, gets default dates
        start = form.cleaned_data['start']
        end = form.cleaned_data['end']        
        account = form.cleaned_data['account']
        hours_transactions = a_models.HoursTransaction.objects.filter(
                             timestamp__range=(start,end))
        if account:
            hours_transactions = hours_transactions.filter(account=account)
    return render_to_response('reporting/hours_balance_changes.html', locals(),
            context_instance=RequestContext(request))


def trans_summary(request):
    """View to summarize transactions by type."""
#    storedays = a_models.StoreDay.objects.all().order_by('-start')

    if request.GET.has_key('start'):
        form = forms.TransactionFilterForm(request.GET)
    else:
        form = forms.TransactionFilterForm()
#        if storedays:
#            form = forms.TransactionFilterForm(data=
#                {'start':storedays[0].start,
#                 'end':datetime.datetime(2099,12,31,23,59,59)})
#        else:
#            form = forms.TransactionFilterForm(data=
#                {'start':datetime.datetime(1900,1,1),
#                 'end':datetime.datetime(2099,12,31,23,59,59)})

    if not form.is_valid():
        transactions = []
        return render_to_response('reporting/transactions_summary.html', 
            locals(), context_instance=RequestContext(request))

#   else form.is_valid():
    account = form.cleaned_data.get('account')
    start = form.cleaned_data.get('start')
    end = form.cleaned_data.get('end')
    list_each = form.cleaned_data.get('list_each')
    filter_type = form.cleaned_data.get('type')
    note = form.cleaned_data.get('note')

    if account:
        transactions = a_models.Transaction.objects.filter(timestamp__range=(start, end)).filter(account=account)
    else:
        transactions = a_models.Transaction.objects.filter(timestamp__range=(start, end))

    if filter_type:
        transactions = transactions.filter(Q(purchase_type=filter_type) | 
                                           Q(payment_type=filter_type))
    if note:
        transactions = transactions.filter(note__icontains=note)

    # add up the totals.  This should become a helper function to use elsewhere.
    starting_total = a_models.total_balances_on(start)
    ending_total = a_models.total_balances_on(end)

    purchases_by_type = []
    purchases_total = 0
    for (code, type) in a_models.PURCHASE_CHOICES:
        total_by_type = transactions.filter(purchase_type=code).aggregate(
                        Sum('purchase_amount')).values()[0]
        purchases_by_type.append({'type':type, 'total':total_by_type})
        purchases_total += total_by_type or 0

    payments_by_type = []
    payments_total = 0
    for (code, type) in a_models.PAYMENT_CHOICES:
        total_by_type = transactions.filter(payment_type=code).aggregate(
                        Sum('payment_amount')).values()[0]
        payments_by_type.append({'type':type, 'total':total_by_type})
        payments_total += total_by_type or 0

    # accounting gibberish for Dan
    start_plus_purchases = starting_total + purchases_total
    end_plus_payments = ending_total + payments_total

    # by default, show the transactions that have notes
    if list_each == False and filter_type == '' and note == '':
        transactions = transactions.filter(note__gt='')

    return render_to_response('reporting/transactions_summary.html', locals(),
            context_instance=RequestContext(request))


def turnout(request):
    ''' shift turnout, using begin and end dates from the daterange form '''
    if request.method == 'POST':
        form = forms.DateRangeForm(request.POST)
        if form.is_valid():
            turnout = s_models.turnout(form.cleaned_data['start'], 
                                       form.cleaned_data['end'])
    else:
        form = forms.DateRangeForm()
        turnout = s_models.turnout(today - datetime.timedelta(30), today)
    return render_to_response('reporting/turnout.html', locals(),
            context_instance=RequestContext(request))


def equity_old(request):
    ''' member equity, grouped by account. '''
    accounts = m_models.Account.objects.all().order_by('name')
    esums = a_models.Transaction.objects.filter(purchase_type='O'
            ).values('account','account__name','account__deposit').annotate(esum=Sum('purchase_amount')).order_by('account')
    return render_to_response('reporting/equity_old.html', locals(),
            context_instance=RequestContext(request))

def equity(request):
    ''' member equity, grouped by account'''
    equity_transactions = a_models.Transaction.objects.filter(purchase_type='O')
#    esums = equity_transactions.values(
#            'account','account__name','account__deposit'
#            ).annotate(esum=Sum('purchase_amount')).order_by('account')
#    data = []
#    for esum in esums:
#        acct = m_models.Account.objects.get(id=esum['account'])
#        data.append({
#            'account': acct, # need account object not just acct id
#            'acct_name': esum['account__name'],
#            'acct_deposit': esum['account__deposit'],
#            'acct_esum': esum['esum'],
#        })
    mem_equity_due = m_models.Member.objects.all().aggregate(total=Sum('equity_due'))
    member_equity = m_models.Member.objects.all().aggregate(total=Sum('equity_held'))
    acct_equity = m_models.Account.objects.all().aggregate(total=Sum('deposit'))
    all_equity = member_equity['total'] + acct_equity['total']
    equity_transactions_sum = equity_transactions.aggregate(total=Sum('purchase_amount'))
    return render_to_response('reporting/equity.html', locals(),
            context_instance=RequestContext(request))

def equity_transfer(request):
    ''' member equity, grouped by account'''
    all_equity_transactions = a_models.Transaction.objects.filter(purchase_type='O')
    equity_transactions = all_equity_transactions.filter(account__deposit__gt=0)
    esums = equity_transactions.values(
            'account','account__name','account__deposit'
            ).annotate(esum=Sum('purchase_amount')).order_by('account')
    data = []
    for esum in esums:
        acct = m_models.Account.objects.get(id=esum['account'])
        data.append({ 
            'account': acct, # need account object not just acct id
            'acct_name': esum['account__name'],
            'acct_deposit': esum['account__deposit'],
            'acct_esum': esum['esum'],
        })
    member_equity = m_models.Member.objects.all().aggregate(total=Sum('equity_held'))
    acct_equity = m_models.Account.objects.all().aggregate(total=Sum('deposit'))
    all_equity = member_equity['total'] + acct_equity['total']
    equity_transactions_sum = all_equity_transactions.aggregate(total=Sum('purchase_amount'))
    return render_to_response('reporting/equity_transfer.html', locals(),
            context_instance=RequestContext(request))

def logging(request, object_type):
    
    if object_type == "account":
        form_type = forms.AccountLoggingFilterForm
        model_type = m_models.Account
        object_repr = "membership.Account"
    elif object_type == "member":
        form_type = forms.MemberLoggingFilterForm
        model_type = m_models.Member
        object_repr = "membership.Member"
#    elif object_type == 'user':
#        form_type = forms.UserLoggingFilterForm
#        model_type = User
#        object_repr = "auth.User"
    else:
        return HttpResponse("Logging report not supported for object type '" + object_type + "'")

    if request.GET.has_key('start'):
        form = form_type(request.GET)
    else:
        form = form_type()

    if not form.is_valid():
        logs = []
        return render_to_response('reporting/logging.html', 
            locals(), context_instance=RequestContext(request))

    obj = form.cleaned_data.get(object_type)
    start = form.cleaned_data.get('start')
    end = form.cleaned_data.get('end')

    logs = LogEntry.objects.filter(object_repr=object_repr).filter(action_time__range=(start, end))

    if obj:
        logs = logs.filter(object_id=obj.id)

    for log in logs:
        user = User.objects.get(id=log.user_id)
        log.user_name = user.first_name + " " + user.last_name
        log.object_name = unicode(model_type.objects.get(id=log.object_id))

        if object_type == 'account':
            log.object_url = reverse('account', args=[log.object_id])
        elif object_type == 'member':
            log.object_url = reverse('member', args=[model_type.objects.get(id=log.object_id).user.username])

    return render_to_response('reporting/logging.html', locals(),
        context_instance=RequestContext(request))

# An attempt to get the historical record of members
# from MESS. Not sure how accurate it is, but the 
# logic is as follows:
# 
# The user enters a date and we pull the members who:
#    - Have a date_joined prior to that date
#    - Either have never departed OR departed after that date
#    - Have been involved in at least one member equity purchase
#      transaction
#
# This is not a perfect system. For example. we have a few 
# proxy shoppers who qualify because while they were once members
# and have purchased equity in the past, they currently are not
# officially members and have no equity.
#
def historical_members(request):
  if request.GET.has_key('date'):
    form = forms.HistoricalMembersForm(request.GET)

    if not form.is_valid():
      return HttpResponse("Please enter in a valid date")

    date = str(form.cleaned_data.get('date'))

    query = "SELECT * from membership_member where date_joined <= '" + date + "' AND (date_departed is null and equity_held>0) OR (date_departed > '" + date + "' AND id in (SELECT DISTINCT member_id FROM accounting_transaction WHERE purchase_type='O' AND purchase_amount>0))"

    members = m_models.Member.objects.raw(query)
    member_count = len(__builtin__.list(members))

  else:
    form = forms.HistoricalMembersForm()

  return render_to_response('reporting/historical_members.html', locals(),
    context_instance=RequestContext(request))
