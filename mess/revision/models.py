import inspect

from django.db import models
from django.contrib.auth.models import User

from mess.membership import models as m_models
from mess.events import models as e_models
from mess.scheduling import models as s_models

class RevisionModel(models.Model):
  """
  Base class for all revision models.
  
  Main reason to create a base class is 
  to overload the == operator. When 
  compared, revisions should be judged 
  equal if their content is equal, not their
  primary key ids (which is the default in
  comparing django models)
  """

  def __eq__(self, other):
    """
    Two revisions are equal if the fields specified 
    in the eq_fields property are equal. 

    eq_fields are either basic types OR managers 
    if the field is a ManyToMany field.
    """

    if type(self) != type(other):
      return False

    for i in range(len(self.eq_fields)):
      if isinstance(self.eq_fields[i], models.manager.Manager):

        s_objects = self.eq_fields[i].order_by('id')
        o_objects = other.eq_fields[i].order_by('id')

        if len(s_objects) != len(o_objects):
          return False

        for s,o in zip(s_objects, o_objects):
          if s.id != o.id:
            return False

      else:
        if self.eq_fields[i] != other.eq_fields[i]:
          return False

    return True

  @property
  def eq_fields(self):
    """
    Defaul eq_fields default to ID, which is the default
    comparison field for django models as a whole
    """
    return [id]

class MemberRevision(RevisionModel):

  member = models.ForeignKey(m_models.Member, related_name="member_revisions")
  user = models.ForeignKey(User)
  status = models.CharField(max_length=1, null=True)
  work_status = models.CharField(max_length=1, null=True)
  has_key = models.BooleanField(default=False)
  date_joined = models.DateField(null=True)
  date_missing = models.DateField(blank=True, null=True)
  date_departed = models.DateField(blank=True, null=True)
  date_turns_18 = models.DateField(blank=True, null=True)
  card_number = models.CharField(max_length=128, blank=True, null=True)
  card_facility_code = models.CharField(max_length=128, blank=True, null=True)
  card_type = models.CharField(max_length=128, blank=True, null=True)
  equity_held = models.DecimalField(max_digits=8, decimal_places=2, null=True)
  equity_due = models.DecimalField(max_digits=8, decimal_places=2, null=True)
  equity_increment = models.DecimalField(max_digits=8, decimal_places=2, null=True)
  referral_source = models.CharField(max_length=20, blank=True, null=True)
  referring_member = models.ForeignKey(m_models.Member, blank=True, null=True)
  orientation = models.ForeignKey(e_models.Orientation, blank=True, null=True)
  job_interests = models.ManyToManyField(s_models.Job)
  skills = models.ManyToManyField(s_models.Skill)
  availability = models.IntegerField(null=True)
  extra_info = models.CharField(max_length=255, blank=True, null=True)
  timestamp = models.DateTimeField(auto_now_add=True)

  @classmethod
  def create_member_revision(cls, member=None):
    member_revision = cls()

    if member:
      member_revision.member = member
      member_revision.user = member.user
      member_revision.status = member.status
      member_revision.work_status = member.work_status
      member_revision.has_key = member.has_key
      member_revision.date_joined = member.date_joined
      member_revision.date_missing = member.date_missing
      member_revision.date_departed = member.date_departed
      member_revision.date_turns_18 = member.date_turns_18
      member_revision.card_number = member.card_number
      member_revision.card_facility_code = member.card_facility_code
      member_revision.card_type = member.card_type
      member_revision.equity_held = member.equity_held
      member_revision.equity_due = member.equity_due
      member_revision.equity_increment = member.equity_increment
      member_revision.referral_source = member.referral_source
      member_revision.referring_member = member.referring_member
      member_revision.orientation = member.orientation
      member_revision.availability = member.availability
      member_revision.extra_info = member.extra_info

      member_revision.save()

      for job_interest in member.job_interests.all():
        member_revision.job_interests.add(job_interest)

      for skill in member.skills.all():
        member_revision.skills.add(skill)

      member_revision.save()

    return member_revision

  @property
  def eq_fields(self):
    return [
        self.member, 
        self.user, 
        self.status,
        self.work_status,
        self.has_key,
        self.date_joined,
        self.date_missing,
        self.date_departed,
        self.date_turns_18,
        self.card_number,
        self.card_facility_code,
        self.card_type,
        self.equity_held,
        self.equity_due,
        self.equity_increment,
        self.referral_source,
        self.referring_member,
        self.orientation,
        self.availability,
        self.extra_info,
        self.job_interests,
        self.skills,
        ]

class AccountRevision(RevisionModel):
  account = models.ForeignKey(m_models.Account, related_name="account_revisions")
  name = models.CharField(max_length=50)
  members = models.ManyToManyField(m_models.Member, related_name='historical_accounts')
  can_shop = models.BooleanField()
  ebt_only = models.BooleanField()
  hours_balance = models.DecimalField(max_digits=5, decimal_places=2)
  deposit = models.DecimalField(max_digits=8, decimal_places=2)
  balance_limit = models.DecimalField(max_digits=8, decimal_places=2)
  note = models.TextField(blank=True)
  shared_address = models.BooleanField()
  timestamp = models.DateTimeField(auto_now_add=True)

  @classmethod
  def create_account_revision(cls, account=None):
    account_revision = cls()

    if account:
      account_revision.account = account
      account_revision.name = account.name
      account_revision.can_shop = account.can_shop
      account_revision.ebt_only = account.ebt_only
      account_revision.hours_balance = account.hours_balance
      account_revision.deposit = account.deposit
      account_revision.balance_limit = account.balance_limit
      account_revision.note = account.note
      account_revision.shared_address = account.shared_address

      account_revision.save()

      for member in account.members.all():
        account_revision.members.add(member)

      account_revision.save()
      
    return account_revision

  @property
  def eq_fields(self):
    return [
      self.account,
      self.name,
      self.members,
      self.can_shop,
      self.ebt_only,
      self.hours_balance,
      self.deposit,
      self.balance_limit,
      self.note,
      self.shared_address,
      ]
