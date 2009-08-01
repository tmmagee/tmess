from datetime import date, timedelta
import datetime
import time

from django.contrib.auth.decorators import user_passes_test
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Template, Context
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.aggregates import Sum

from mess.accounting import models as a_models
from mess.accounting.models import Transaction
from mess.membership import models as m_models
from mess.scheduling import models as s_models
from mess.scheduling.views import old_rotations
#from mess.accounting.models import get_credit_choices, get_debit_choices
#from mess.accounting.models import get_trans_total
from mess.reporting import forms

from mess.utils.search import list_usernames_from_fullname

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

@user_passes_test(lambda u: u.is_staff)
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
        ('Email without @', mems.filter(emails__isnull=False).exclude(emails__email__contains='@')),
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

@user_passes_test(lambda u: u.is_staff)
def contact(request):
    context = RequestContext(request)
    members = m_models.Member.objects.active().filter(accountmember__shopper=False)
    context['emailable'] = members.filter(emails__isnull=False)
    context['nonemailable'] = members.exclude(emails__isnull=False)
    template = get_template('reporting/contact.html')
    return HttpResponse(template.render(context))


@user_passes_test(lambda u: u.is_staff)
def reports(request):
    # each named category can have various reports, each with a name and url
    past90d = datetime.date.today() - datetime.timedelta(90)
    report_categories = [{'name':cat_name, 'reports':
            [{'name':rpt_name, 'url':url} for rpt_name, url in cat_rpts] 
            } for cat_name, cat_rpts in [

        ('Accounts',[
            listrpt('Accounts','Active Contacts',
                '',
                '{% for y in x.accountmember_set.all %}{% if y.member.is_active %}{{ y.member }}{% if y.account_contact %}*{% endif %}{% if y.shopper %}(s){% endif %}<br>{% endif %}{% endfor %}\*=Deposit, (s)=Shopper\r\n'+
                '{% for y in x.members.active %}{% for z in y.phones.all %}{{ y.user.first_name }}: {{ z }}<br>{% endfor %}{% endfor %}\Phones\r\n'+
                '{% for y in x.members.active %}{% for z in y.emails.all %}{{ y.user.first_name }}: {{ z }}<br>{% endfor %}{% endfor %}\Emails\r\ndeposit'),
                
# broken :(
#           listrpt('Accounts','Needing Shifts? Incomplete List',
#               'task__time__gte!='+str(datetime.date.today())+'\r\nmembers__work_status__in!=ec',
#               'note'),

# this duplicates all multi-member accounts :(
#           listrpt('Accounts','With A Member On LOA',
#               'members__leaveofabsence__start__lte='+str(datetime.date.today())+'\r\nmembers__leaveofabsence__end__gte='+str(datetime.date.today()),
#               '{% for m in x.members.all %}{% for l in m.leaveofabsence_set.all %}{{ m }}: LOA {{ l.start }} until {{ l.end }}<br>{% endfor %}{% endfor %}\\Members\r\nnote',
#               order_by='members__leaveofabsence__end'),

            listrpt('Accounts','With No Proxy Shoppers',
                'accountmember__shopper!=True', 'members\r\nactive_member_count'),

            listrpt('Accounts','With At Least $50 Deposit',
                'deposit__gte=50.00', 'deposit'),

#           listrpt('Accounts','Frozen',
#               'can_shop=False', 
#               'can_shop\r\ndeposit\r\nbalance\r\nhours_balance'),

            listrpt('Accounts','Owing 1 Hour or More',
                'hours_balance__gte=1.00', 'hours_balance\r\nnote'),

        ]),

        ('Members',[

            listrpt('Members','with Email',
                'emails__isnull=False', 'accounts\r\nemails\r\nBox:emails',
                order_by='accounts'),

            listrpt('Members','without Email (phone list)',
                'emails__isnull=True\r\naccountmember__shopper=False',
                'accounts\r\nphones', order_by='accounts'),

            listrpt('Members','Depositors on LOA',
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
                'accounts\r\ndate_joined',
                order_by='-date_joined'),

            listrpt('Members','Recently Departed',# (since '+past90d.strftime('%B %e, %Y')+')',
                'date_departed__gte='+str(past90d), 
                'accounts\r\ndate_joined\r\ndate_departed',
                order_by='-date_departed',
                include_inactive='on'),
        ]),

        ('Accounting',[
            ('Cash Sheets',reverse('cashsheet')),

            listrpt('Accounts','All Balances and Deposits',
                '','balance\r\ndeposit\r\nactive_member_count',
                include_inactive='on'),

            listrpt('Accounts','Active Balances and Deposits',
                '','balance\r\ndeposit\r\nactive_member_count'),

            ('Transaction Summary',reverse('trans_summary')),

            ('Dues and Deposits Billing',reverse('billing')),
        ]),

        ('Tasks',[
            ('Wall Calendar', reverse('scheduling-rotation')),

            listrpt('Tasks','Cashiers With Email',
                'job__name=Cashier\r\nmember__isnull=False',
                'job\r\nmember\r\naccount\r\nmember.emails\r\nBox:member.emails'),

            listrpt('Tasks','Storekeepers',
                'job__name=Store Keeper\r\nmember__isnull=False',
                'job\r\nmember\r\naccount'),

            listrpt('Tasks','Unfilled Next 7 Days',
                'member__isnull=True\r\nexcused=False\r\ntime__lte='+
                    str(datetime.date.today()+datetime.timedelta(days=7)),
                'job'),

        ]),

        ('Member Work',[
            ('Member Work Dashboard', reverse('memberwork')),
            ('Need Shift', reverse('memberwork')+'?section=Need Shift'),
            ('Regular Shift', reverse('memberwork')+'?section=Regular Shift'),
            ('Exemptions', reverse('memberwork')+'?section=Exempt'),
            ('Committee', reverse('memberwork')+'?section=Committee'),
        ]),

        ('Anomalies',[
            ('Page For Fixing "Deposit Holder" and "Shopper"',
                reverse('accountmemberflags')),
            ('Database Anomalies',reverse('anomalies')),
        ]),

        ('Old Reports',[
            ('Member Contact Information', reverse('contact_list')),

            listrpt('Accounts','Accounts With Permanent Shifts',
                'task__time__year='+str(datetime.date.today().year+1),
                '{% for m in x.members.all %}{{ m }}: {{ m.next_shift }}<br>{% endfor %}\\Shifts by Member\r\nnote'),

            listrpt('Accounts','Accounts With A Work Exemption',
                'members__work_status=e',
                '{% for m in x.members.all %}{{ m }}: {{ m.get_work_status_display }}<br>{% endfor %}\\Members\r\nnote'),

            listrpt('Accounts','Accounts With Committee Work',
                'members__work_status=c',
                '{% for m in x.members.all %}{{ m }}: {{ m.get_work_status_display }}<br>{% endfor %}\\Members\r\nnote'),

            listrpt('Accounts','Electors (use Active Contacts instead)',
                '',
                '{% for y in x.accountmember_set.all %}{{ y.member }}{% if y.account_contact and not y.member.date_departed and not y.member.date_missing %}*{% endif %}<br>{% endfor %}\\*=Elector\r\nactive_member_count\r\ndeposit'),

        ]),
        ]]
    return render_to_response('reporting/reports.html', locals(),
            context_instance=RequestContext(request))

def listrpt(object, desc, filter, output, include_inactive='', order_by=''):
    return (desc, reverse('list')+'?'+urlencode(locals()))

@user_passes_test(lambda u: u.is_staff)
def list(request):
    template = get_template('reporting/list.html')
    context = RequestContext(request)
    context['form'] = forms.ListFilterForm(request.GET)
    context['errors'] = []
    if request.GET.has_key('desc'):
        context['desc'] = request.GET['desc']

    for requestfield in ['object','include_inactive','filter','order_by','output']:
        if request.GET.has_key('object') and context['form'].is_valid():
            context[requestfield] = context['form'].cleaned_data[requestfield]
        else:
            context[requestfield] = ''
    
    if context['object'] == 'Accounts':
        if context['include_inactive']:
            objects = m_models.Account.objects.all()
        else:
            objects = m_models.Account.objects.active()
        blank_object = m_models.Account()
        outputters = [ListOutputter('', blank_object, 'Account')]
    elif context['object'] == 'Members':
        if context['include_inactive']:
            objects = m_models.Member.objects.all()
        else:
            objects = m_models.Member.objects.active()
        blank_object = m_models.Member()
        outputters = [ListOutputter('', blank_object, 'Member')]
    elif context['object'] == 'Tasks':
        objects = s_models.Task.objects.all()
        if not context['include_inactive']:
            # show only tasks in the next 6 weeks...
            objects = objects.filter(time__range=(datetime.date.today(),datetime.date.today()+datetime.timedelta(weeks=6)))
            # ...or in the next 4 weeks if we're sure it's a 4-week rotation
            objects = objects.exclude(time__gt=datetime.date.today()+datetime.timedelta(weeks=4), recur_rule__interval=4)
        blank_object = s_models.Task()
        outputters = [ListOutputter('<a href="{% url scheduling-task x.id %}">{{ x }}</a>', blank_object, 'Task')]
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
            context['textarea'] = [y.render(x) for x in objects]
        else:
            outputters.append(ListOutputter(outfield, blank_object))

    context['result'] = [[y.render(x) for y in outputters] for x in objects]
    context['totals'] = [y.total for y in outputters[1:]]
    context['outputfieldnames'] = outputters
    return HttpResponse(template.render(context))

class ListOutputter:
    def __init__(self, field, blank_object, name=None):
        self.field = field
        self.total = 0
        self.name = name or field.title()
        if '{' in field:
            self.render = self.render_as_template
            if '\\' in field:
                self.field, self.name = field.split('\\',1)
            self.template = Template(self.field)
        else:
            if self.field:
                self.fieldpath = self.field.split('.')
            else:
                self.fieldpath = []
            self.render = self.render_by_getattr

    def render_as_template(self, object):
        object_context = Context({'x':object})
        try:
            return self.template.render(object_context)
        except:
            return 'error: '+self.field
        
    def render_by_getattr(self, object):
        for pathpiece in self.fieldpath:
            if not hasattr(object, pathpiece):
                return 'error: '+self.field
            object = getattr(object, pathpiece)
        if hasattr(object, 'all'):
            return mark_safe(u'<br>'.join([self._render_obj(relobj) 
                                           for relobj in object.all()]))
        else:
            return self._render_obj(object)

    def _render_obj(self, object):
        if hasattr(object, 'get_absolute_url'):
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

@user_passes_test(lambda u: u.is_staff)
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
        'Exempt', 'LOA', 'Need Shift', 'Proxy Shift Pairs', 'Proxy']
    if 'section' in request.GET:
        section_names = [request.GET['section']]
    sections = [{'name':x, 
                 'memberwork':[mw for mw in memberwork if mw.section == x]} 
               for x in section_names]
    return render_to_response('reporting/memberwork.html', locals(),
            context_instance=RequestContext(request))

def prepmemberwork(member, weekbreaks):
    # return this very member object, but just add things onto it.
    shift = member.task_set.filter(time__gte=datetime.date.today(), 
            recur_rule__isnull=False).order_by('time')
    if shift.count():
        shift = shift[0]
        shift.rotletter = old_rotations(shift.time, shift.recur_rule.interval)
    else:
        shift = None
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


@user_passes_test(lambda u: u.is_staff)
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


@user_passes_test(lambda u: u.is_staff)
def transaction_report(request):
    """View to summarize transactions by type."""
    if request.GET.has_key('start'):
        form = forms.TransactionFilterForm(request.GET)
    else:
        form = forms.TransactionFilterForm()
    if form.is_valid():
#    if request.GET.has_key('start') and form.is_valid():
        start = form.cleaned_data.get('start')
        end = form.cleaned_data.get('end')
        list_each = form.cleaned_data.get('list_each')
    else:
        start = datetime.date.today()
        end = start + datetime.timedelta(1)
        list_each = False
    transactions = a_models.Transaction.objects.filter(
                   timestamp__range=(start, end))

    # add up the totals.  This should become a helper function to use elsewhere.
    purchases_by_type = []
    grand_total = 0
    for (code, type) in a_models.PURCHASE_CHOICES:
        total_by_type = transactions.filter(purchase_type=code).aggregate(
                        Sum('purchase_amount')).values()[0]
        purchases_by_type.append({'type':type, 'total':total_by_type})
        grand_total += total_by_type or 0
    purchases_by_type.append({'type':'Total Purchases', 'total':grand_total})

    payments_by_type = []
    grand_total = 0
    for (code, type) in a_models.PAYMENT_CHOICES:
        total_by_type = transactions.filter(payment_type=code).aggregate(
                        Sum('payment_amount')).values()[0]
        payments_by_type.append({'type':type, 'total':total_by_type})
        grand_total += total_by_type or 0
    payments_by_type.append({'type':'Total Payments', 'total':grand_total})

    return render_to_response('reporting/transactions_summary.html', locals(),
            context_instance=RequestContext(request))

