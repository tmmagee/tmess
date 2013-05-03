import datetime, time, calendar
from dateutil.relativedelta import relativedelta

#from django.conf import settings
#from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext, Context
from django.template.loader import get_template
from django.utils import simplejson
import django.views.decorators.vary as vary
from django.forms.formsets import formset_factory
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core import mail

from mess.scheduling import forms, models
from mess.membership import forms as m_forms
from mess.membership import models as m_models
from mess.core.permissions import has_elevated_perm

MEMBER_COORDINATOR_EMAIL = 'membership@mariposa.coop'

today = datetime.date.today()
todaytime = datetime.datetime.now()

@login_required
def myschedule(request):
    context = RequestContext(request)
    member = request.user.get_profile()
    account = member.get_primary_account()
    if request.method == 'POST' and request.POST.get('action') == 'Sign me up!':
        shift = get_object_or_404(models.Task, id=request.POST.get('task'))
        # error here means a race condition -- user should reload page
        assert shift.member is None and shift.account is None
        if shift.time < todaytime + datetime.timedelta(1):
            return HttpResponse('Sorry, online signup is only available at least 1 day in advance.  You may still be able to sign up for this shift by going to the co-op.')
        if shift.recur_rule:
            shift = shift.excuse_and_duplicate()  # one-time fill
        shift.member = member
        shift.account = account
        shift.makeup = True
        shift.save()
    account_shifts = account.task_set.filter(
                     time__range=(today,today+datetime.timedelta(180)))
    my_shift = member.regular_shift()
    if my_shift:
        similar_assigned = models.Task.objects.filter(job=my_shift.job,
                           recur_rule__isnull=False,
                           time__range=(today,today+datetime.timedelta(42)),
                           hours=my_shift.hours,
                           member__isnull=False)
        unassigned = models.Task.objects.filter(member__isnull=True,
                 job=my_shift.job,
                 excused=False,
                 time__range=(today,today+datetime.timedelta(20)))
    else:
        similar_assigned = []
        unassigned = []

    context["is_workingmember"] = member.work_status == 'w' or member.work_status == 'c'

    return render_to_response('scheduling/myschedule.html', locals(),
                              context_instance=context)

def unassigned_days(firstday, lastday):
    """
    Pass in a range of days, get back a dict of days with count of 
    unassigned tasks
    """
    days = {}
    format = "%m/%d/%Y"
    tasks = models.Task.objects.unassigned().filter(
            time__gte = firstday,
            time__lte = lastday
    )
    for task in tasks:
        datestr = task.time.strftime(format)
        days[datestr] = days.get(datestr, 0) + 1
    #for task in models.Task.recurring.unassigned():
    #    occur_times = task.get_occur_times(firstday, lastday)
    #    for occur_time in occur_times:
    #        datestr = occur_time.strftime(format)
    #        days[datestr] = days.get(datestr, 0) + 1
    return days
    
def unassigned_for_month(request, month):
    try:
#        date = datetime.datetime.strptime(month, "%Y-%m") Python 2.4 workaround
        date = datetime.datetime(*time.strptime(month, "%Y-%m")[0:5])
    except ValueError:
        raise Http404
    firstday = date + relativedelta(day=1)
    lastday = date + relativedelta(day=31)
    days = unassigned_days(firstday, lastday)
    return HttpResponse(simplejson.dumps(days))

def task(request, task_id):
    task = get_object_or_404(models.Task, id=task_id)
#   date = str(task.time.date())
    return HttpResponseRedirect(reverse('scheduling-schedule', 
                    args=[task.time.date()])+'?jump_to_task_id='+str(task_id))

@login_required
def schedule(request, date=None):
    context = RequestContext(request)

    if not has_elevated_perm(request, 'scheduling', 'add_task'):
        return HttpResponseRedirect(reverse('welcome'))

    if date:
        try:
#            date = datetime.datetime.strptime(date, "%Y-%m-%d") Python 2.4 workaround
            date = datetime.datetime(*time.strptime(date, "%Y-%m-%d")[0:5])
        except ValueError:
            raise Http404
    else:
        today = datetime.date.today()
        # need datetime object for rrule, but datetime.today is, like, now
        date = datetime.datetime(today.year, today.month, today.day)
    add_time = date + datetime.timedelta(hours=9)
    add_task_form = forms.TaskForm(instance=models.Task(time=add_time), 
            prefix='add')
    add_recur_form = forms.RecurForm(prefix='recur-add')
    tasks = models.Task.objects.filter(time__year=date.year).filter(
            time__month=date.month).filter(time__day=date.day).order_by(
            'time', 'hours', 'job', '-recur_rule')
    prepared_tasks = []
    for index, task in enumerate(tasks):
        task.form = forms.TaskForm(instance=task, prefix=str(index))
        task.recur_form = forms.RecurForm(instance=task.recur_rule, 
                prefix='recur-%s' % index)
        prepared_tasks.append(task)

    if request.method == 'POST':
        if 'save-add' in request.POST:
            task_form = add_task_form = forms.TaskForm(request.POST, 
                    prefix='add')
            recur_form = add_recur_form = forms.RecurForm(request.POST, 
                    prefix='recur-add')
        else:
            task_index = request.POST.get('task-index')
            task = prepared_tasks[int(task_index)]
            if 'duplicate' in request.POST:
                task.excused = True
                task.save()
                task.duplicate()
                return HttpResponseRedirect(reverse('scheduling-schedule', 
                        args=[date.date()]))
            elif 'remove' in request.POST:
                if task.recur_rule:
                    future_tasks = task.recur_rule.task_set.filter(
                            time__gt=task.time)
                    for future_task in future_tasks:
                        future_task.delete()
                task.delete()
                return HttpResponseRedirect(reverse('scheduling-schedule', 
                        args=[date.date()]))
            task_form = task.form = forms.TaskForm(request.POST, 
                    instance=task, prefix=task_index)
            recur_form = task.recur_form = forms.RecurForm(request.POST, 
                    instance=task.recur_rule, prefix='recur-%s' % task_index)
        if task_form.is_valid() and recur_form.is_valid():
            task = task_form.save()
            if recur_form.changed_data:
                frequency = recur_form.cleaned_data['frequency']
                interval = recur_form.cleaned_data['interval']
                until = recur_form.cleaned_data['until']
                task.set_recur_rule(frequency, interval, until)
                task.update_buffer()
            return HttpResponseRedirect(reverse('scheduling-schedule', 
                    args=[date.date()]))

    # else... if request.method != POST
    elif request.GET.has_key('jump_to_task_id'):
        try:
            context['jump_to_task_id'] = int(request.GET['jump_to_task_id'])
        except:
            pass

    context['date'] = date
    a_day = datetime.timedelta(days=1)
    context['previous_date'] = date - a_day
    context['next_date'] = date + a_day
    firstday = date + relativedelta(day=1)
    lastday = date + relativedelta(day=31)
    context['cal_json']  = simplejson.dumps(unassigned_days(firstday, lastday))

    context['tasks'] = prepared_tasks
    context['add_task_form'] = add_task_form
    context['add_recur_form'] = add_recur_form
    # to include autocomplete js media files:
    context['form'] = {'media':add_task_form.media}
    template = loader.get_template('scheduling/schedule.html')
    return HttpResponse(template.render(context))

# filter for date
@login_required
def timecard(request, date=None):
    context = RequestContext(request)
    context['messages'] = []

    if not has_elevated_perm(request, 'scheduling', 'add_timecard'):
        return HttpResponseRedirect(reverse('welcome'))

    if date:
        try:
#            date = datetime.datetime.strptime(date, "%Y-%m-%d")  Python 2.4 workaround
            date = datetime.datetime(*time.strptime(date, "%Y-%m-%d")[0:5])
        except ValueError:
            raise Http404
    else:
        today = datetime.date.today()
        # need datetime object for rrule, but datetime.today is, like, now
        date = datetime.datetime(today.year, today.month, today.day)
# It seems our ordering was not deterministic enough, and that caused the 
# 'Task with this None already exists' if the request.POST and the queryset 
# ended up with different ordering.  Fixed by adding order_by 'id'.  -Paul
    tasks = models.Task.objects.filter(time__range=(
        datetime.datetime.combine(date, datetime.time.min), 
        datetime.datetime.combine(date, datetime.time.max))).exclude(
        account__isnull=True, excused=True).order_by('time', 'hours', 'job',
        '-recur_rule', 'id')

    TimecardFormSet = formset_factory(forms.TimecardForm)

    if request.method == 'POST':
      formset = TimecardFormSet(request.POST)

      for n in range(0, formset.total_form_count()):
        form = formset.forms[n]

        if (form.is_valid()):
          task = models.Task.objects.get(id=form.cleaned_data['id'])

          '''
          It's possible for a task to exist with out a member attached to it. 
          This shouldn't happen, but if it does don't save anything or email
          anyone. Just continue on to the next task
          '''
          if not task.member:
            continue

          context['task'] = task

          '''
          Automatic email for excused shifts or unexcused shifts
          Only goes out if this is the first the timecard has been submitted
          '''
          if task.hours_worked is None:
            shift_status = form.cleaned_data['shift_status']

            '''
            Per Jamila and Shinara, we only send out emails if the task is not 
            a make up or banked shift
            '''
            if (shift_status == 'excused' or shift_status == 'unexcused') and not task.makeup and not task.banked:
              if task.job.name.strip() == "Committee":
                email_template = get_template("scheduling/emails/shift_" + shift_status + "_committee.html")
                subject_template = get_template("scheduling/emails/shift_" + shift_status + "_committee_subject.html")
              elif task.job.name.strip() == "Mill Creek Farm":
                email_template = get_template("scheduling/emails/shift_" + shift_status + "_mill_creek.html")
                subject_template = get_template("scheduling/emails/shift_" + shift_status + "_mill_creek_subject.html")
              else:
                email_template = get_template("scheduling/emails/shift_" + shift_status + ".html")
                subject_template = get_template("scheduling/emails/shift_" + shift_status + "_subject.html")

              subject = ''.join(subject_template.render(context).splitlines())

              if task.member:
                if task.member.user.email:
                  mail.send_mail(
                    subject,
                    email_template.render(context), 
                    MEMBER_COORDINATOR_EMAIL, 
                    [task.member.user.email]
                    )

                context['messages'].append(
                  "Shift " + shift_status + " email sent to member %s %s of account %s" % (
                  task.member.user.first_name, 
                  task.member.user.last_name, 
                  task.account.name
                  ))

          task.hours_worked=form.cleaned_data['hours_worked']

          task.excused = (form.cleaned_data['shift_status']=='excused')
          task.makeup = form.cleaned_data['makeup']
          task.banked = form.cleaned_data['banked']
          task.reminder_call = form.cleaned_data['reminder_call']
          task.save()

        else:
          ''' 
          Even if we don't validate, we still save the reminder call value, as
          reminder calls take place a day before the timecard is ready to be submitted.
          '''
          task = models.Task.objects.get(id=request.POST['form-' + str(n) + '-id'])
          task.reminder_call = request.POST['form-' + str(n) + '-reminder_call']
          task.save()

      if (not formset.errors):
        return HttpResponseRedirect(reverse('scheduling-timecard', args=[date.date()]))
    else:
      num_tasks = unicode(len(tasks))

      data = {
        'form-TOTAL_FORMS': num_tasks,
        'form-INITIAL_FORMS': num_tasks,
        'form-MAX_NUM_FORMS': num_tasks,
      }

      for i in range(len(tasks)):
        task = tasks[i];
        data['form-' + str(i) + '-id'] = task.id;

        if (task.hours_worked):
          data['form-' + str(i) + '-hours_worked'] = task.hours_worked 
        else:
          data['form-' + str(i) + '-hours_worked'] = 0

        if (task.hours_worked):
          data['form-' + str(i) + '-shift_status'] = u'worked'
        elif (task.excused):
          data['form-' + str(i) + '-shift_status'] = u'excused'
        else:
          data['form-' + str(i) + '-shift_status'] = u'unexcused'

        data['form-' + str(i) + '-hours'] = task.hours
        data['form-' + str(i) + '-makeup'] = task.makeup
        data['form-' + str(i) + '-banked'] = task.banked
        data['form-' + str(i) + '-reminder_call'] = task.reminder_call

      formset = TimecardFormSet(data)
      
    # We used to use a model formset built with the Task 
    # model, so the template expects each form to have 
    # member named instance that points to its corresponding
    # task. We set these manually here - TM 1/17/2012
    for i in range(len(formset.forms)):
      formset.forms[i].instance = tasks[i]  

    context['formset'] = formset
    context['date'] = date
    a_day = datetime.timedelta(days=1)
    context['previous_date'] = date - a_day
    context['next_date'] = date + a_day
    context['old_rotations'] = old_rotations(date)
    context['turnout'] = models.turnout(date.date())
    template = loader.get_template('scheduling/timecard.html')
    return HttpResponse(template.render(context))

def old_rotations(date, interval=None):
    cycle_begin = datetime.datetime(2009,1,26)
    delta = (date - cycle_begin).days
    fourweek = 'ABCD'[int(delta/7) % 4]
    sixweek = 'EFGHIJ'[int(delta/7) % 6]
    eightweek = 'MNOPQRKL'[int(delta/7) % 8]
    if interval == 4:
        return fourweek
    elif interval == 6:
        return sixweek
    else:
        return ', '.join([fourweek, sixweek, eightweek])

@login_required
def rotation(request):
    """
    Print listings of shifts according to rotation cycles.
    We'll assume a shift is permanent if it's scheduled 10 rotations ahead.
    We try to match each 4-week shift to an 'ideal' slot on week of 1990-01-01.
    I'm hard-coding pagebreaks because page-break-inside:avoid; doesn't work.
    """ 
    context = RequestContext(request)
    horizon = 10
    rotationtables = []

    if request.GET.has_key('job'):
        rotation_filter_form = forms.RotationFilterForm(request.GET)
    else:
        rotation_filter_form = forms.RotationFilterForm()

    if rotation_filter_form.is_valid():
        job = rotation_filter_form.cleaned_data.get('job')
    else:
        job = False

    # get four-week rotations, idealizing them
    for weekday in range(0,7):
        table = {'freq':4, 'weekday':weekday, 'cycles':[], 
                 'dayname':calendar.day_name[weekday], 'pagebreakafter':True}
        table['idealdate'] = idealdate = datetime.date(1990, 1, 1+weekday)

        if job:
            table['ideals'] = models.Task.objects.filter(time__range=(
                datetime.datetime.combine(idealdate, datetime.time.min),
                datetime.datetime.combine(idealdate, datetime.time.max))).filter(job=job)
        else:
            table['ideals'] = models.Task.objects.filter(time__range=(
                datetime.datetime.combine(idealdate, datetime.time.min),
                datetime.datetime.combine(idealdate, datetime.time.max)))
        for cycle in range(4):
            column = cyclecolumn(4, weekday, cycle, False, False, job)
            idealize(column['shifts'], table['ideals'])
            table['cycles'].append(column)
        rotationtables.append(table)

    # get six-week cashier rotations
#    for weekday in range(0,7):
#        table = {'freq':6, 'weekday':weekday, 'cycles':[], 'cashier6':True,
#                 'dayname':calendar.day_name[weekday]}
#        if weekday in [2,4,6]:
#            table['pagebreakafter'] = True
#        for cycle in range(6):
#            table['cycles'].append(cyclecolumn(6, weekday, cycle, cashieronly=True))
#        rotationtables.append(table)

    # get dancer shifts, idealizing them
    table = {'freq':4, 'dayname':'Dancer (by Sunday)', 
             'dancer':True, 'cycles':[]}
    table['idealdate'] = idealdate = datetime.date(1990, 1, 8)

    if not job:
        table['ideals'] = models.Task.objects.filter(time__range=(
                datetime.datetime.combine(idealdate, datetime.time.min),
                datetime.datetime.combine(idealdate, datetime.time.max)))
        
        for cycle in range(4):
            column = cyclecolumn(4, 6, cycle, getdancers=True)
            idealize(column['shifts'], table['ideals'])
            table['cycles'].append(column)
        rotationtables.append(table)

    context['rotation_filter_form'] = rotation_filter_form
    context['rotationtables'] = rotationtables

    template = loader.get_template('scheduling/rotation.html')
    return HttpResponse(template.render(context))

def cyclecolumn(freq, weekday, cycle, getdancers=False, cashieronly=False, job=False):
    horizon = 7
    cycle_begin = datetime.datetime(2009,1,26)
    today = datetime.date.today()
    first = cycle_begin + datetime.timedelta(days=weekday+7*cycle)
    while first.date() < today:
        first += datetime.timedelta(days=7*freq)
    column = {}
    column['dates'] = [first + datetime.timedelta(days=7*freq*i)
        for i in range(horizon)]
    if freq == 4:
        column['letter'] = 'ABCD'[cycle]
    elif freq == 6:
        column['letter'] = 'EFGHIJ'[cycle]
    lastdate = (column['dates'][-1]).date()
    shifts = models.Task.objects.filter(time__range=(
              datetime.datetime.combine(lastdate, datetime.time.min),
              datetime.datetime.combine(lastdate, datetime.time.max)),
              recur_rule__interval=freq, recur_rule__frequency='w',)
    if getdancers:
        shifts = shifts.filter(job__name__icontains='dancer')
    else:
        shifts = shifts.exclude(job__name__icontains='dancer')
    if cashieronly:
        shifts = shifts.filter(job__name='Cashier')
    if job:
        shifts = shifts.filter(job=job)

    column['shifts'] = shifts.order_by('time','job')
    return column

def idealize(actualshifts, idealshifts):
    """
    Append the one best actual shift (or none) to each idealshift.actuals array
    Mark actual shifts as .idealized=True.
    We want to select the best matches, for example:
          ideal(9am)---actual(10am)    ideal(2pm)---actual(3pm)
          ideal(9am)---actual(10am)    ideal(2pm)-----None
          ideal(9am)---actual(10am)       None------actual(3pm)
          ideal(9am)-----None          ideal(2pm)---actual(3pm)
       but still match:     ideal(9am)---actual(3pm)
    To approximate this, we do several passes with increasing tolerance. 
    """
    for ideal in idealshifts:
        try:
            ideal.actuals.append(None)
        except AttributeError:
            ideal.actuals = [None]
        if actualshifts:
            ideal.actualizeddatetime = datetime.datetime.combine(
                    actualshifts[0].time.date(), 
                    ideal.time.time())
    for tolerance_hours in [0, 1, 4, 16]:
        tolerance = datetime.timedelta(hours=tolerance_hours)
        for ideal in idealshifts:
            if ideal.actuals[-1]:   # already matched on better tolerance
                continue
            for actual in actualshifts:
                if hasattr(actual, 'idealized'):
                    continue
                if actual.job != ideal.job:
                    continue
                timediff = abs(ideal.actualizeddatetime - actual.time)
                if timediff <= tolerance:
                    ideal.actuals[-1] = actual
                    actual.idealized = True
                    actual.timediff = timediff.seconds
                    break

def jobs(request):
    context = {
        'jobs': models.Job.objects.all().exclude(type='x')
    }
    return render_to_response('scheduling/jobs.html', context,
                                context_instance=RequestContext(request))

def job(request, job_id):
    context = {
        'jobs': models.Job.objects.filter(id=job_id)
    }
    return render_to_response('scheduling/jobs.html', context,
                                context_instance=RequestContext(request))

def job_edit(request, job_id=None):
    if job_id:
        job = get_object_or_404(models.Job, id=job_id)
    else:
        job = models.Job()
    is_errors = False
    ret_resp = HttpResponseRedirect(reverse('scheduling-jobs'))
    
    if request.method == 'POST':
        if 'cancel' in request.POST:
            return ret_resp

        job_form = forms.JobForm(request.POST, instance=job)
        if job_form.is_valid():
            job_form.save()
            return ret_resp
        else:
            is_errors = True
    else:
        job_form = forms.JobForm(instance=job)

    context = {
        'job': job,
        'is_errors': is_errors,
        'job_form': job_form,
        'add': job_id==None,
    }
    return render_to_response('scheduling/job_form.html', context,
                                context_instance=RequestContext(request))

@login_required
def job_descriptions(request):
    context = RequestContext(request)
    context['title'] = "Job Descriptions"
    context['items'] = models.Job.objects.all().filter(type='o').order_by('name')
    return render_to_response('scheduling/item_descriptions.html', context)

def generate_reminder(day):
    '''generates tasks that receive reminder on a given day.
    used by the reminder email cron as well as the function below.'''

    TD_NORMAL = 3
    TD_DANCER = 9
    targetDay = day + datetime.timedelta(TD_NORMAL)
    dancerTargetDay = day + datetime.timedelta(TD_DANCER)

    normalTasks = models.Task.objects.not_dancer().filter(
        time__range=(targetDay, targetDay+datetime.timedelta(1)),
        member__isnull=False)
    dancerTasks = models.Task.objects.dancer().filter(
        time__range=(dancerTargetDay, dancerTargetDay+datetime.timedelta(1)),
        member__isnull=False)
    return (normalTasks | dancerTasks)

def reminder(request, date=None):
    '''
    displays the reminder emails sent on the given date.
    '''
    
    if date:
        date = datetime.date(*time.strptime(date, "%Y-%m-%d")[:3])
    else:
        date = datetime.date.today()
    previous_date = date - datetime.timedelta(1)
    next_date = date + datetime.timedelta(1)

    tasks = generate_reminder(date)
    noemail = tasks.filter(member__user__email='').distinct()
    tasks = tasks.exclude(member__user__email='').distinct()

    return render_to_response('scheduling/reminder.html', locals(),
                                context_instance=RequestContext(request))

@login_required
def switch(request):
    id = request.GET.get('original')
    try:
        original = get_object_or_404(models.Task, id=id)
    except ValueError:
        raise Http404
    if original.member is None or ((original.member.user != request.user)
                                   and not request.user.is_staff):
        return HttpResponse('Sorry.  You are not assigned to that task.')
    if original.makeup:
        return HttpResponse('Sorry.  Cannot switch a make-up shift.')
    SOONEST_SWITCH = datetime.timedelta(2)
    earliest_switch = datetime.datetime.now()# + SOONEST_SWITCH
    if original.time < earliest_switch:
        return HttpResponse('Sorry.  Cannot switch shifts within %s' % SOONEST_SWITCH)
    if request.method == 'POST':
        switch = models.Task.objects.get(id=request.POST['task'])
        if switch.member or switch.account:
            return HttpResponse('Sorry.  Switch task is already assigned.')
        if switch.recur_rule:
            switch = switch.excuse_and_duplicate()  # one-time fill
        original.excuse_and_duplicate()
        switch.member = original.member
        switch.account = original.account
        switch.makeup = True
        switch.save()
        return HttpResponseRedirect(reverse('myschedule'))
    form = forms.PickTaskForm()

    # How switching works: 
    #   - Member can choose any available shift for same job 14 days before or after their original shift
    #   - However, if the original shift is less than 14 days away, the earliest possible switch is the 
    #     one day after the switch is made
    #   - One big issue: currently members can currently switch for shifts that are part of recurring jobs
    #     and so it's possible (if that recurring job gets filled by another member) that two members
    #     will be assigned for the same shift on the same day. Dana and I are just going to assume this 
    #     will be rare for now - Tom Magee
    earliest_date = original.time - datetime.timedelta(14)
    if earliest_date < earliest_switch:
        earliest_date = earliest_switch
    possible_switches = models.Task.objects.filter(
                time__range=(earliest_date, original.time + datetime.timedelta(14)),
                hours=original.hours, 
                excused=False,
                job=original.job, 
                account__isnull=True, 
                member__isnull=True,
                )
    form.fields['task'].queryset = possible_switches
    return render_to_response('scheduling/switch.html', locals(),
                              context_instance=RequestContext(request))

def trade(request):
    """ 
    two members trade shifts (one-time), and tell a staff person 
    uses member.remove_from_shifts to break recur_rules where needed
    """
    original = models.Task.objects.get(id=request.GET['original'])
    if request.method == 'POST':
        trade = models.Task.objects.get(id=request.POST['task'])
        DO_IT_RIGHT = False
        if DO_IT_RIGHT: 
            duporiginal = original.excuse_and_duplicate()
            duporiginal.account = trade.account
            duporiginal.member = trade.member
            duporiginal.save()
            duptrade = trade.excuse_and_duplicate()
            duptrade.account = original.account
            duptrade.member = original.member
            duptrade.save()
        else: # Do it wrong, breaking the recur_rules into halves
            original_account = original.account
            original_member = original.member
            original_member.remove_from_shifts(original.time.date(), 
                            original.time.date()+datetime.timedelta(1))
            trade_account = trade.account
            trade_member = trade.member
            trade_member.remove_from_shifts(trade.time.date(), 
                        trade.time.date()+datetime.timedelta(1))
            original.account = trade_account
            original.member = trade_member
            original.recur_rule = None
            original.save()
            trade.account = original_account
            trade.member = original_member
            trade.recur_rule = None
            trade.save()
        return HttpResponseRedirect(reverse('scheduling-schedule', 
                                    args=[original.time.date()]))
    if 'member' in request.GET:   # member to trade with
        trade_member = m_models.Member.objects.get(id=request.GET['member'])
        form = forms.PickTaskForm()
        form.fields['task'].queryset = models.Task.objects.filter(
                   member=trade_member, 
                   time__range=(today - datetime.timedelta(7),
                                today + datetime.timedelta(180)))
        form.fields['task'].initial = form.fields['task'].queryset[0].id
    else:
        form = m_forms.PickMemberForm()
    return render_to_response('scheduling/trade.html', locals(),
                              context_instance=RequestContext(request))
        
def skills(request):
    context = RequestContext(request)

    # allow new skill to be added, i.e. include little form
    ret_resp = HttpResponseRedirect(reverse('scheduling-skills'))
    if request.method == 'POST':    #form was submitted
        if 'cancel' in request.POST:
            return ret_resp
        skill_form = forms.SkillForm(request.POST)
        if skill_form.is_valid():
            skill_form.save()
            return ret_resp
    else:
        skill_form = forms.SkillForm()

    context['skills'] = models.Skill.objects.all().exclude(type='x')
    context['skill_form'] = skill_form
    template = loader.get_template('scheduling/skills.html')
    return HttpResponse(template.render(context))

def skill_edit(request, skill_id=None):
    ret_resp = HttpResponseRedirect(reverse('scheduling-skills'))
    is_errors = False
    if skill_id:
        skill = get_object_or_404(models.Skill, id=skill_id)
    else:
        skill = models.Skill()

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return ret_resp
        skill_form = forms.SkillForm(request.POST, instance=skill)
        if skill_form.is_valid():
            skill_form.save()
            return ret_resp
        else:
            is_errors = True

    else:
        skill_form = forms.SkillForm(instance=skill)

    context = {
        'skill': skill,
        'is_errors': is_errors,
        'skill_form': skill_form,
        'add': skill_id==None,
        }

    return render_to_response('scheduling/skill_form.html', context,
                                context_instance=RequestContext(request))

@login_required
def skill_descriptions(request):
    context = RequestContext(request)
    context['title'] = "Skill Descriptions"
    context['items'] = models.Skill.objects.all().order_by('name')
    return render_to_response('scheduling/item_descriptions.html', context)

# unused below

#def _task_template_save(proto_form, worker_formset):
#    task_template = proto_form.save(commit=False)
#    for form in worker_formset.forms:
#        #task_data = form.cleaned_data.copy()
#        #if not task_data['id']:
#        #    del task_data['id']
#        task = models.Task(**form.cleaned_data)
#        task.time = task_template.time
#        task.hours = task_template.hours
#        # TODO: set frequency and interval of recur_rule
#        #task.frequency = task_template.frequency
#        #task.interval = task_template.interval
#        task.job = task_template.job
#        task.save()
#
    # convert QuerySet to list for appending recurring tasks
    #task_list = list(tasks)
    #recurring_tasks = models.Task.recurring.all()
    #for task in recurring_tasks:
    #    occur_times = task.get_occur_times(date, date + a_day)
    #    for occur_time in occur_times:
    #        task_list.append(task)

    # group tasks by same job, time, and hours
    #task_groups = []
    #for task in tasks:
    #    group_found = False
    #    for group in task_groups:
    #        if (task.time == group[0] and task.hours == group[1] and 
    #                task.job == group[2] and task.recur_rule == group[3]):
    #            group[4].append(task)
    #            group_found = True
    #            continue
    #    if not group_found:
    #        task_groups.append((task.time, task.hours, task.job, 
    #                task.recur_rule, [task]))
    #task_groups.sort()

    # make it easier to get to things in the template
    #task_group_dicts = []
    #for index, group in enumerate(task_groups):
    #    tasks = []
    #    for task in group[4]:
    #        if task.member and task.account:
    #            tasks.append((task.member.user.get_full_name(), 
    #                    task.account.name, task))
    #        else:
    #            tasks.append((None, None, task))
    #    tasks.sort()
    #    tasks = [task[2] for task in tasks]
    #    first_task = tasks[0]
    #    form = forms.TaskForm(instance=first_task, prefix='%s' % index)
    #    task_dicts = []
    #    for task in tasks:
    #        if task.member and task.account:
    #            task_dicts.append({'taskid': task.id, 'member': task.member.id, 
    #                    'account': task.account.id})
    #        else:
    #            task_dicts.append({'taskid': task.id, 'member': '', 'account': ''})
    #    worker_formset = forms.WorkerFormSet(initial=task_dicts, 
    #            prefix='%s-worker' % index)
    #    group_dict = {'first_task': first_task, 'tasks': tasks, 'form': form,
    #            'worker_formset': worker_formset}
    #    task_group_dicts.append(group_dict)

#def assign(request):
#    date = datetime.date.today()
#    context = {
#        'tasks': models.Task.objects.filter(deadline__year=date.year, deadline__month=date.month)
#    }
#    return render_to_response('scheduling/assign.html', context,
#                                context_instance=RequestContext(request))

#task crud
#task_dict =  {
#    'model': models.Task,
#    'login_required': True,
#}
#
#def update_task(request, **kwargs):
#    up_dict = dict(task_dict)
#    up_dict.update(kwargs)
#    return update_object(request, post_save_redirect=reverse('scheduling-schedule'), **up_dict)
#
#def delete_task(request, **kwargs):
#    del_dict = dict(task_dict)
#    del_dict.update(kwargs)
#    return delete_object(request, post_delete_redirect=reverse('scheduling-schedule'), **del_dict)
#
#def add_task(request, task_id=None):
#    context = {}
#
#    if task_id == None:
#        context = {
#            'task_form': forms.TaskForm(),
#        }
#    else:
#        task = models.Task.objects.get(id__exact=task_id)
#        context = {
#            'task_form': forms.TaskForm(instance=task),
#            'task': task,
#        }
#    
#    return render_to_response('scheduling/task_form.html', context,
#                                context_instance=RequestContext(request))
#
#def task_list(request, date=None):
#    "return an html snippet listing tasks for the selected day"
#    if date == None:
#        date = datetime.date.today()
#    else:
#        year, month, day = date.split('-')
#        date = datetime.date(int(year), int(month), int(day))
#    
#    context = {
#        'tasks': models.Task.objects.filter(deadline__year=date.year, deadline__month=date.month, deadline__day=date.day)
#    }
#    return render_to_response('scheduling/snippets/task_list.html', context,
#                                context_instance=RequestContext(request))
#                                
#def open_task_list(request, date=None):
#    "return an html snippet listing all open tasks for the selected day"
#    if date == None:
#        date = datetime.date.today()
#    else:
#        year, month, day = date.split('-')
#        date = datetime.date(int(year), int(month), int(day))
#    
#    context = {
#        'tasks': models.Task.objects.filter(deadline__year=date.year, deadline__month=date.month, deadline__day=date.day)
#    }
#    return render_to_response('scheduling/snippets/open_task_list.html', context,
#                                context_instance=RequestContext(request))
#
#def open_task_list_month(request, date=None):
#    "return an html snippet listing all days with open tasks for a specified month"
#    if date == None:
#        date = datetime.date.today()
#    else:
#        year, month = date.split('-')
#        date = datetime.date(int(year), int(month))
#    
#    context = {
#        'tasks': models.Task.objects.filter(deadline__year=date.year, deadline__month=date.month, member='null')
#    }
#    return render_to_response('scheduling/snippets/open_task_list_month.html', context,
#                                context_instance=RequestContext(request)
#    )

