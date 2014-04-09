import datetime
import string
from decimal import Decimal

from django import forms
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Min

# import scheduling models to figure what tasks a member has
from mess.scheduling import models as s_models
from mess.utils.dateutils import quarter_diff, round_to_quarter

ACCOUNT_TYPE = (
    ('m', 'Member'),
    ('o', 'Organization'),
)

MEMBER_STATUS = (
    ('a', 'Active'),
    ('L', 'Leave of Absence'),
    ('m', 'Missing'),  # Member has disappeared without notice.
    ('x', 'Missing Delinquent'),  # Member has disappeared, owing money/time
    ('d', 'Departed'),
#   ('i', 'Inactive'),
)
WORK_STATUS = (
    ('w', 'Workshift'),  # Member is active and should have a workshift
    ('c', 'Committee'), # Anything not tracked shift by shift
    ('e', 'Exempt'),     # Exemptions granted for kids, health, etc.
    ('n', 'No-Workshift'), # Non-working member
    ('x', 'Non-Member'), # Not a member - only for our Non-Member account
)
EXEMPTION_TYPES = (
    ('k', 'Kids'),
    ('s', 'Seniors'),
    ('c', 'Caretaker'),
    ('p', 'Single Parent'),
    ('h', 'Health'),
    ('S', 'Special'),
)
ADDRESS_TYPES = (
    ('h','Home'),
    ('w','Work'),
    ('o','Other'),
)
PHONE_TYPES = (
    ('h','Home'),
    ('w','Work'),
    ('m','Mobile'),
    ('o','Other'),
)
EMAIL_TYPES = (
    ('p','Personal'),
    ('w','Work'),
    ('s','School'),
    ('o','Other'),
)

REFERRAL_SOURCES = (
    ('',''),
    ('Current Member','Current Member'),
    ('Website','Website'),
    ('Flyer','Flyer'),
    ('Advertisement','Advertisement'),
    ('Walked By','Walked By'),
    ('Other','Other'),
)

EQUITY_PAID_OPTIONS = (
    ('',''),
    ('200','$200 (Full Equity)'),
    ('25','$25 (Partial Equity)'),
    ('50','$50 (Partial Equity)'),
    ('100','$100 (Partial Equity)'),
    ('300','$300 (Additional Equity)'),
    ('500','$500 (Additional Equity)'),
    ('0','I will pay my equity later'),
)

MEMBER_AVAILABILITY_SUNDAY = (
    (0x1, 'Morning'),
    (0x2, 'Afternoon'),
    (0x4, 'Evening'),
)

MEMBER_AVAILABILITY_MONDAY = (
    (0x8, 'Morning'),
    (0x10, 'Afternoon'),
    (0x20, 'Evening'),
)

MEMBER_AVAILABILITY_TUESDAY = (
    (0x40, 'Morning'),
    (0x80, 'Afternoon'),
    (0x100, 'Evening'),
)

MEMBER_AVAILABILITY_WEDNESDAY = (
    (0x200, 'Morning'),
    (0x400, 'Afternoon'),
    (0x800, 'Evening'),
)

MEMBER_AVAILABILITY_THURSDAY = (
    (0x1000, 'Morning'),
    (0x2000, 'Afternoon'),
    (0x4000, 'Evening'),
)

MEMBER_AVAILABILITY_FRIDAY = (
    (0x8000, 'Morning'),
    (0x10000, 'Afternoon'),
    (0x20000, 'Evening'),
)

MEMBER_AVAILABILITY_SATURDAY = (
    (0x40000, 'Morning'),
    (0x80000, 'Afternoon'),
    (0x100000, 'Evening'),
)

today = datetime.date.today()

class MemberManager(models.Manager):
    'Custom manager to add extra methods'
    def active(self):
        return self.filter(date_missing__isnull=True, 
                           date_departed__isnull=True)

    def inactive(self):
        return self.filter(Q(date_missing__isnull=False)|
                           Q(date_departed__isnull=False))

    def present(self):
        return self.active().exclude(leaveofabsence__in=
                                     LeaveOfAbsence.objects.current())

class Member(models.Model):
    user = models.ForeignKey(User, unique=True)
    status = models.CharField(max_length=1, choices=MEMBER_STATUS,
                            default='a')
    work_status = models.CharField(max_length=1, choices=WORK_STATUS,
        default='w', help_text='This only matters for Active Members. \
        Workshift means they should have a workshift. \
        Committee means anything not tracked as a \
        regular shift, for example, COMMITTEE, BUSINESS/ORG, etc')
    has_key = models.BooleanField(default=False)
    #primary_account = models.ForeignKey('Account', blank=True, null=True)
    date_joined = models.DateField(default=datetime.date.today())
    date_missing = models.DateField(blank=True, null=True)
    date_departed = models.DateField(blank=True, null=True)
    date_turns_18 = models.DateField(blank=True, null=True)
    card_number = models.CharField(max_length=128, blank=True, null=True)
    card_facility_code = models.CharField(max_length=128, blank=True, 
            null=True)
    card_type = models.CharField(max_length=128, blank=True, null=True)

    member_owner_equity_held = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    membership_fund_equity_held = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    equity_due = models.DecimalField(max_digits=8, decimal_places=2, default=25)
    equity_increment = models.DecimalField(max_digits=8, decimal_places=2, default=25)

    referral_source = models.CharField(max_length=20, choices=REFERRAL_SOURCES, blank=True, null=True)
    referring_member = models.ForeignKey('self', blank=True, null=True)
    orientation = models.ForeignKey('events.Orientation', blank=True, null=True)

    job_interests = models.ManyToManyField(s_models.Job)
    skills = models.ManyToManyField(s_models.Skill)

    # This field will actually just capture a bit array that captures a member's
    # availability choices. Bit array is captured in MEMBER_AVAILABILITY dictionary
    # declared above
    availability = models.IntegerField(null=True)

    # This field will hold extra information
    extra_info = models.CharField(max_length=255, blank=True, null=True)

    hours_balance = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    member_card = models.CharField(max_length=12, blank=True, null=True)

    objects = MemberManager()

    def __unicode__(self):
        return self.user.get_full_name()

    def equity_target(self):
        '''
        Returns the member's equity target. A member's equity target is $200 
        with the following exceptions:
        - $0 if they are only a proxy shopper
        - $150 if house is three or more people
        - $125 if house is five or more people
        '''
        shared_house_size = 0

        for acct in self.accounts.filter(shared_address=True):
            shared_house_size = max(shared_house_size, acct.active_member_count)

        # If this member is an account contact on any account, then they are 
        # a member of the co-op (not just a proxy shopper) and they owe equity
        only_a_proxy = len(AccountMember.objects.filter(member=self.id, account_contact=True)) == 0

        if only_a_proxy:
            return Decimal("0.00")
        elif shared_house_size >= 5:
            return Decimal("125.00")
        elif shared_house_size >= 3:
            return Decimal("150.00")

        return Decimal("200.00")
    
    '''
    This function calculates the "real" equity increment, factoring in 
    equity payments that are made ahead of schedule
    '''
    def calc_real_equity_increment(self, equity_increment, equity_held, equity_target, date_joined):
      quarter_joined = round_to_quarter(date_joined)  
      current_quarter = round_to_quarter(datetime.datetime.today())
      quarters = quarter_diff(current_quarter, quarter_joined)
      on_track_equity = min(equity_increment * quarters, equity_target)

      if (equity_held >= on_track_equity):
        return Decimal(0)
      elif (on_track_equity - equity_held) < equity_increment:
        return on_track_equity - equity_held
      else:
        return equity_increment

    def potential_new_equity_due(self):
        if (not self.is_active) or (self.is_on_loa):
          return Decimal(0)

        real_equity_increment = self.calc_real_equity_increment(self.equity_increment, self.equity_held, self.equity_target(), self.date_joined)
        held_plus_due = self.equity_held + self.equity_due
        remaining_to_target = self.equity_target() - held_plus_due
        if remaining_to_target < 0:
          remaining_to_target = Decimal(0)
        return min(real_equity_increment, remaining_to_target)

    def untrained(self):
        return s_models.Skill.objects.exclude(
            trained_by__task__in=self.task_set.worked()).distinct()

    def qualified_tasks(self, possible=None):
        if possible is None:
            possible = s_models.Task.objects.unassigned_future()
        return possible.exclude(job__skills_required__in=self.untrained())
        

    def get_hours_balance_history_url(self):
        return reverse('member_hours_balance_changes')+'?member='+str(self.id)

    @property 
    def equity_held(self):
      return self.member_owner_equity_held + self.membership_fund_equity_held

    @property
    def current_loa(self):
        loa_set = self.leaveofabsence_set.current()
        if loa_set.count():
            return loa_set[0]
        
    @property
    def is_active(self):
        return not (self.date_missing or self.date_departed)

    @property
    def is_on_loa(self):
        return bool(self.current_loa)

    @property
    def is_cashier_recently(self):
        shifts_recently = self.task_set.filter(time__range=(
            datetime.date.today()-datetime.timedelta(180), datetime.date.today()))
        cashier_shifts_recently = shifts_recently.filter(job__name__in=[
            'Cashier','After Hours Billing'], hours_worked__gt=0)
        return bool(cashier_shifts_recently.count())

    @property
    def is_cashier_today(self):
        shifts_today = self.task_set.filter(time__range=(
            datetime.date.today(), datetime.date.today()+datetime.timedelta(1)))
        cashier_shifts_today = shifts_today.filter(job__name__in=[
            'Cashier','After Hours Billing'])
        return bool(cashier_shifts_today.count())

    @property
    def name(self):
        return self.user.username

    @models.permalink
    def get_absolute_url(self):
        return ('member', [self.user.username])

    def next_shift(self):
        tasks = self.task_set.filter(time__gte=datetime.date.today())
        if tasks.count():
            return tasks[0]

    def regular_shift(self):
        tasks = self.task_set.filter(time__gte=datetime.date.today(),
                recur_rule__isnull=False)
        if tasks.count():
            return tasks[0]

    def remove_from_shifts(self, start, end=None):
        '''
        Removes member from workshifts that haven't happened yet.
        End date is optional.
        '''

        # handle start and end dates in the past
        if start < datetime.date.today():
            start = datetime.date.today()
        if end and end < datetime.date.today():
            return          # end date in past; don't mess with shifts.

        # switch all post-start tasks to new recur rule; 
        # set old recur_rule.until as our start date.
        tasks = self.task_set.filter(time__gte=start)
        r_rule_switch = {}
        for task in tasks:
            if task.recur_rule:
                if task.recur_rule in r_rule_switch:
                    new_rule = r_rule_switch[task.recur_rule]
                else:
                    new_rule = task.duplicate_recur_rule()
                    task.recur_rule.until = start
                    task.recur_rule.save()
                    r_rule_switch[task.recur_rule] = new_rule
                task.recur_rule = new_rule

            # task is inside LOA and should be released for one-time fill.
            # i.e. no longer point to any recur rule
            if end:
                if task.time.date() <= end:
                    task.recur_rule = None
                    task.member = task.account = None
                    
            # permanently remove from workshift (no end date)
            else:
                task.member = task.account = None

            task.save()

    def get_primary_account(self):
        try:
            primary = self.accounts.filter(
                    accountmember__shopper=False)[0]
        except IndexError:
            try:
                primary = self.accounts.all()[0]
            except IndexError:
                primary = Account()
        return primary

    def autocomplete_label_member(self):
        return '%s %s' % (self.user.first_name, self.user.last_name) 

    def autocomplete_label(self):
        if self.is_active:
            return '%s %s (%s)' % (self.user.first_name, self.user.last_name, 
                               self.get_primary_account().name)
        else:
            return '* %s %s (%s)' % (self.user.first_name, self.user.last_name,
                                self.get_primary_account().name)

    @property
    def verbose_status(self):
        if self.date_departed:
            return 'Departed since %s' % self.date_departed
        elif self.date_missing:
            return 'Missing since %s' % self.date_missing
        else:
            if self.is_on_loa:
                return 'Active, but on leave until %s' % self.current_loa.end
            return 'Active'

    def date_joined_is_realistic(self):
        if self.date_joined > datetime.date(1970,1,1):
            return self.date_joined

    def date_orientation(self):
        orientations = self.task_set.filter(job__name='Orientation Attendee')
        if orientations.count():
            return orientations[0].time.date()

    def save(self, *args, **kwargs):
        if self.date_departed:

          # If the person who is departing is _really_ 
          # departing (and we are not just using that date
          # as a marker as we do with new accounts that
          # are departed by default) then we set their 
          # equity_due to 0 by the finance department's 
          # request. 1971 is Mariposa's first year.

          if self.date_departed.year >= 1971:
            self.equity_due = Decimal(0)

        super(Member, self).save(*args, **kwargs)

    def excused_hours_owed(self):
        return self.hours_balance > self.hours_balance.to_integral_value()

    def unexcused_hours_owed(self):
        if self.hours_balance.to_integral_value() >= 1:
            return True
        else:
            return False

    def is_in_group(self, group):
      for g in self.user.groups.all():
        if g.name==group:
          return True
      return False


    @property
    def is_organization(self):
      for g in self.user.groups.all():
        if g.name=='organization':
          return True
      return False

    class Meta:
        ordering = ['user__username']

class LeaveOfAbsenceManager(models.Manager):
    def current(self):
        return self.filter(start__lte=today, end__gt=today)

class LeaveOfAbsence(models.Model):
    """ Leave of absence periods for members. """
    member = models.ForeignKey(Member)
    start = models.DateField()
    end = models.DateField(help_text="Remember!: Editing a Leave of absense directly does not affect member's workshifts.  Please remove them manually from any workshifts that fall within the leave.")
    objects = LeaveOfAbsenceManager()
    


class WorkExemption(models.Model):
    """ Work exemptions for members. """
    type = models.CharField(max_length=1, choices=EXEMPTION_TYPES, default='k')
    member = models.ForeignKey(Member)
    start = models.DateField()
    end = models.DateField()


class AccountManager(models.Manager):
    'Custom manager to add extra methods'
    def active(self):
        return self.filter(accountmember__in=
                           AccountMember.objects.active_depositor()).distinct()

    def inactive(self):
        return self.exclude(accountmember__in=
                            AccountMember.objects.active_depositor())

    def present(self):   # will show up on cash sheets
        return self.filter(accountmember__in=
                           AccountMember.objects.present_depositor()).distinct()

class Account(models.Model):
    name = models.CharField(max_length=50, unique=True)
    #contact = models.ForeignKey(Member, related_name='contact_for')
    members = models.ManyToManyField(Member, related_name='accounts', 
            through='AccountMember')
    can_shop = models.BooleanField(default=True)
    ebt_only = models.BooleanField()
    hours_balance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # deposit is now known as equity
    deposit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # balance is updated with each transaction.save()
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    shared_address = models.BooleanField(default=False)
    balance_limit = models.DecimalField(max_digits=8, decimal_places=2, default=5.00)
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPE, default='m')

    objects = AccountManager()

    def alphanumericname(self):
        return ''.join(c for c in self.name if c in string.letters+string.digits+' ')[:50]

    def active_members(self):
        return Member.objects.filter(accountmember__in=
                self.accountmember_set.active_depositor())

    @property
    def active_member_count(self):
        return self.active_members().count()

    def billable_members(self):
        ''' active depositors MINUS anyone on leave of absence '''
        return Member.objects.filter(accountmember__in=
                self.accountmember_set.present_depositor())

    @property
    def billable_member_count(self):
        return self.billable_members().count()

    @property
    def has_staff_member(self):
      for member in self.members.all():
        for group in member.user.groups.all():
          if group.name=='staff':
            return True

      return False

    @property
    def discount(self):
        # active working members at 10%
        # active nonworking members at 5%
        # LOA members and proxy shoppers not included
        totaldiscount = 0.0
        memberset = self.billable_members()
        if memberset.count() == 0:
          return 0

        for m in memberset:
          if m.is_in_group('staff'):
            totaldiscount += 20.0
          elif m.work_status == 'x':
            totaldiscount += 0.0
          elif m.work_status != 'n':
            totaldiscount += 10.0
          else: 
            totaldiscount += 5.0

        rounded = round(totaldiscount / memberset.count(), 2)
        # no decimals if can be displayed as integer
        return rounded if int(rounded) != rounded else int(rounded)


    def autocomplete_label(self):
        if self.active_member_count:
            return self.name
        else:
            return '* '+self.name

    @models.permalink
    def get_absolute_url(self):
        return ('account', [self.id])

    def get_hours_balance_history_url(self):
        return reverse('account_hours_balance_changes')+'?account='+str(self.id)

    @models.permalink
    def get_templimit_url(self):
        return ('templimit', [self.id])

    def members_leaveofabsence_set(self):
        return LeaveOfAbsence.objects.filter(member__accounts=self)

    def recent_cashier(self):
        return self.task_set.filter(job__name='Cashier', time__range=(
            today - datetime.timedelta(120), today))
    
    def workhist(self):
        '''
        Generates the work history object used to produce the workhistory calendar on account page.
        complex data structures here:
        workhist[] is an array of weeks
        each week is a {} dictionary of {'days':[array], 'tasks':[array], 
           'newmonth' and 'newyear'} (newmonth and newyear flags show month 
           alongside the calendar)
        each day is a {} dictionary of {'week':(parent-pointer), 'date':(number),
           'workflag':(flag for highlighting), 'task':last-task}
        '''
        workhist = []
        dayindex = {}
        today = datetime.date.today()
        lastsunday = today - datetime.timedelta(days=today.weekday()+1)
        try:
            oldesttime = self.task_set.all().order_by('time')[0].time
            oldestweeks = ((today - oldesttime.date()).days / 7) + 2
            oldestweeks = max(oldestweeks, 16)
        except IndexError:
            oldestweeks = 16
        for weeksaway in range(-oldestweeks,52):
            week = {'tasks':[]}
            if weeksaway == -12:
                week['flagcurrent'] = True
            elif weeksaway == 7:
                week['flagfuture'] = True
            firstday = lastsunday + datetime.timedelta(days=7*weeksaway)
            week['days'] = [{'week':week} for i in range(7)]
            for i in range(7):
                week['days'][i]['date'] = firstday + datetime.timedelta(days=i)
                dayindex[week['days'][i]['date']] = week['days'][i]
            if 7 <= week['days'][6]['date'].day < 14:
                week['newmonth'] = week['days'][6]['date']
            elif 14 <= week['days'][6]['date'].day < 21:
                week['newyear'] = week['days'][6]['date'].year
            workhist.append(week)
        for task in self.task_set.all():
            if task.time.date() in dayindex:
                day = dayindex[task.time.date()]
                if 'workflag' in day:
                    day['workflag'] = 'complex-workflag'
                else:
                    day['workflag'] = task.simple_workflag
                day['task'] = task
                day['week']['tasks'].append(task)
        for leave in self.members_leaveofabsence_set():
            for dayofleave in daterange(leave.start, leave.end):
                if dayofleave not in dayindex: 
                    continue
                day = dayindex[dayofleave]
                if 'workflag' not in day:
                    day['workflag'] = 'LOA'
        dayindex[today]['istoday'] = True
        return workhist        

    def next_shift(self):
        tasks = self.task_set.filter(time__gte=datetime.date.today())
        if tasks.count():
            return tasks[0]

    def verbose_balance(self):
        if self.balance > 0:
            return 'Owes %.2f' % self.balance
        elif self.balance < 0:
            return 'Has credit of (%.2f)' % -self.balance
        else:
            return 'Zero balance'

    def owes_money(self):
        if self.balance > 0:
            return True
        else:
            return False

    def excused_hours_owed(self):
        return self.hours_balance > self.hours_balance.to_integral_value()

    def unexcused_hours_owed(self):
        if self.hours_balance.to_integral_value() >= 1:
            return True
        else:
            return False

    # this is no longer used by accounting.models, and can probably be removed
    def balance_on(self, time):
        newest_trans = self.transaction_set.filter(
                       timestamp__lt=time).order_by('-timestamp')
        if newest_trans.count():
            return newest_trans[0].account_balance

    def days_old(self):
        oldest = self.members.active().aggregate(Min('date_joined')).values()[0]
        if oldest is None:  # in case of no members or other problem
            return -1
        return (datetime.date.today() - oldest).days

    def months_old(self):
        return self.days_old() / 30
        
    def max_allowed_to_owe(self):
        if self.temporarybalancelimit_set.current():
            return self.temporarybalancelimit_set.current()[0].limit
        else:
            return self.balance_limit
    max_allowed_balance = property(max_allowed_to_owe)

    def must_pay(self):
        max_allowed_to_owe = self.max_allowed_to_owe()
        if self.balance > max_allowed_to_owe:
            return self.balance - max_allowed_to_owe

    def way_over_limit(self):
        way_limit = 2 * self.max_allowed_to_owe()
        if self.balance > way_limit:
            return self.balance - way_limit

    def must_work(self):
        if self.hours_balance > Decimal('0.03'):
            return self.hours_balance

    def obligations(self):
        obligations = self.billable_member_count
        if not obligations:
            if self.active_member_count:
                return 'ON LEAVE'
            return
        for am in self.accountmember_set.all():
            if (am.member.regular_shift()
                    or (am.member.work_status in 'ecn' and not am.shopper)):
                obligations -= 1
        if obligations:
            return 'NEEDS SHIFT'

    def frozen_flags(self):
        if self.name == 'One-Time Shopper':
            return
        flags = []
        if self.balance > self.max_allowed_to_owe():
            flags.append('Owes Balance')
        if self.hours_balance > Decimal('0.03'):
            flags.append('Owes Hours')
        if not self.can_shop:
            flags.append('CANNOT SHOP')
        obligations = self.billable_member_count
        if not obligations:
            if self.active_member_count:
                flags.append('ON LEAVE')
            else:
                flags.append('ACCOUNT CLOSED')
        satisfactions = self.accountmember_set.filter(
            Q(member__work_status__in='ecn', shopper=False) |
            Q(member__task__time__gte=datetime.date.today())).count()
        if obligations > satisfactions and self.days_old() > 7:
            flags.append('NEEDS SHIFT')
        if self.ebt_only:
            flags.append('EBT Only')
        return flags

    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class AccountMemberManager(models.Manager):
    def active_depositor(self):
        return self.filter(shopper=False, member__in=Member.objects.active())

    def present_depositor(self):
        return self.filter(shopper=False, member__in=Member.objects.present())

    def active_shopper(self):
        return self.filter(shopper=True, member__in=Member.objects.active())

    def inactive(self):
        return self.exclude(member__in=Member.objects.active())

class AccountMember(models.Model):
    account = models.ForeignKey(Account)
    member = models.ForeignKey(Member)
    # account_contact displayed as "deposit holder" per shinara's request
    # -- gsf 2009-05-03

    # In retrospect, I think we should assume deposit_holder = not shopper.
    # After we enabled both, we started getting broken cases where 
    # account_contact != not shopper.  --Paul 2009-10-10

    account_contact = models.BooleanField(default=True, verbose_name="deposit holder")
    # primary_account isn't being displayed for now.  not needed according
    # to shinara -- gsf 2009-05-03
    primary_account = models.BooleanField(default=True)
    # is this member just a shopper on the account?
    shopper = models.BooleanField(default=False)

    objects = AccountMemberManager()
    
    def __unicode__(self):
        return u'%s: %s' % (self.account, self.member)

    class Meta:
        ordering = ['account', 'id']
    


class TemporaryBalanceLimitManager(models.Manager):
    def current(self):
        return self.filter(start__lte=today, until__gte=today)

class TemporaryBalanceLimit(models.Model):
    'start and end may not overlap, otherwise result is unpredictable'
    account = models.ForeignKey(Account)
    limit = models.DecimalField(max_digits=5, decimal_places=2)
    start = models.DateField(auto_now_add=True)
    until = models.DateField()

    objects = TemporaryBalanceLimitManager()

    def __unicode__(self):
        return u'%s may owe %s until %s/%s/%s' % (self.account, self.limit, 
            self.until.month, self.until.day, self.until.year)


# possibly include IM and URL classes at some point

class Address(models.Model):
    member = models.ForeignKey(Member, related_name='addresses')
    type = models.CharField(max_length=1, choices=ADDRESS_TYPES, default='h')
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, default='Philadelphia')
    # state is CharField to allow for international
    state = models.CharField(max_length=50, default='PA')
    # postal_code is CharField for the same reason as state
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default='USA')
    
    def __unicode__(self):
        if self.address2:
            return ('%s, %s' % (self.address1, self.address2))
        else:
            return self.address1

    def fullmailing(self):
        ''' return full mailing address, including name and country if not USA '''
        ret = '%s\n%s' % (self.member, self.address1)
        if self.address2:
            ret += '\n%s' % self.address2
        ret += '\n%s, %s %s' % (self.city, self.state, self.postal_code)
        if self.country != 'USA':
            ret += '\n%s' % self.country
        return ret

    class Meta:
        verbose_name_plural = 'Addresses'


class Phone(models.Model):
    member = models.ForeignKey(Member, related_name='phones')
    type = models.CharField(max_length=1, choices=PHONE_TYPES, default='h')
    number = models.CharField(max_length=20)

    def __unicode__(self):
        return self.number

# this is duplicated in scheduling/models.  duplicated to avoid circular imports.
def daterange(start, end):
    while start < end:
        yield start
        start += datetime.timedelta(1)

# this should be a method on Skill, but it can't be due to circular imports
def members_with_skill(skill):
    return Member.objects.present().filter(
        task__in=skill.trainedbytasks()).distinct()

class MemberSignUp(models.Model):

    def __unicode__(self):
        return self.first_name + " " + self.last_name

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=100)
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, default='Philadelphia')
    state = models.CharField(max_length=50, default='PA')
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50, default='USA')
    referral_source = models.CharField(max_length=20, choices=REFERRAL_SOURCES)
    referring_member = models.CharField(max_length=100, blank='true')
    orientation = models.ForeignKey('events.Orientation')
    equity_paid = models.CharField(max_length=20, choices=EQUITY_PAID_OPTIONS)
    saved = models.BooleanField(default=False)
    spam = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
