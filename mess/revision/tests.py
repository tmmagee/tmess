"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from mess.revision import models
from mess.revision import member_revision_has_changes
from mess.revision import account_revision_has_changes
from mess.membership import models as m_models
from mess.scheduling import models as s_models


class MemberRevisionTest(TestCase):

  def create_account(self, name):
    account = m_models.Account(name=name, ebt_only=False)
    account.save()    
    return account

  def create_account_member(self, account, member):
    am = m_models.AccountMember.objects.create(account=account, member=member)
    am.save()
    return am

  def create_user(self, username):

    user = User.objects.get_or_create(username=username)[0]

    user.first_name = "Test"
    user.last_name = "User"
    user.email_address = "noone@nowhere.com"
    user.set_password(User.objects.make_random_password())
    user.save()

    return user


  def add_job_interests(self, member):
    jobs = []
  
    for i in range(2):
      jobs.append(s_models.Job())
      jobs[i].name = member.user.username + str(i)
      jobs[i].description = member.user.username + str(i)
      jobs[i].type = "o"
      jobs[i].deadline = False
      jobs[i].save()
      member.job_interests.add(jobs[i])
    
  def add_skills(self, member):
    skills = []

    for i in range(2):
      skills.append(s_models.Skill())
      skills[i].name = member.user.username + str(i)
      skills[i].type = "o"
      skills[i].save()
      member.skills.add(skills[i])
  
  def create_member(self, username):
    user = self.create_user(username)
    member = m_models.Member()
    member.user = user
    member.status = 'a'
    member.work_status = 'n'
    member.has_key = False
    member.date_joined = '2012-01-01'
    member.date_missing = None
    member.date_departed = None
    member.date_turns_18 = None
    member.card_number = None
    member.card_facility_code = ""
    member.card_type = None
    member.equity_held = 0
    member.equity_due = 0
    member.equity_increment = 25
    member.referral_source = None
    member.referring_member = None
    member.orientation = None
    member.availability = None
    member.extra_info = None

    member.save()

    self.add_job_interests(member)
    self.add_skills(member)

    member.save()

    return member

  def create_job(self, name):
    job = s_models.Job(name=name, deadline=False) 
    job.save()
    return job

  def create_skill(self, name):
    skill = s_models.Skill(name=name)
    skill.save()
    return skill

  def add_job(self, member, job):
    member.job_interests.add(job)

  def add_skill(self, member, skill):
    member.skills.add(skill)

  def test_create_member(self):
    m = self.create_member("tcm")

    self.assertIsNotNone(m.user)
    self.assertIsNotNone(m)
    self.assertIsInstance(m.user, User)
    self.assertIsInstance(m, m_models.Member)

  def test_create_member_revision(self):
    m = self.create_member("tcmr")
    mr1 = models.MemberRevision.create_member_revision(m)

    self.assertIsInstance(mr1, models.MemberRevision)
    self.assertIsInstance(mr1.member, m_models.Member)

  def test_equal_member_revisions(self):
    m = self.create_member("temr")
    job = self.create_job("temr")
    skill = self.create_skill("temr")
    job2 = self.create_job("temr2")
    skill2 = self.create_skill("temr2")
    self.add_job(m, job)
    self.add_skill(m, skill)
    self.add_job(m, job2)
    self.add_skill(m, skill2)
    m.save()
    mr1 = models.MemberRevision.create_member_revision(m)
    mr2 = models.MemberRevision.create_member_revision(m)

    return self.assertEqual(mr1, mr2)

  def test_unequal_member_revisions(self):
    m = self.create_member("tumr")
    mr1 = models.MemberRevision.create_member_revision(m)
    mr1.save()
    self.add_job(m, self.create_job("tumr"))
    mr2 = models.MemberRevision.create_member_revision(m)

    return self.assertNotEqual(mr1, mr2)

  def test_equal_account_revisions(self):
    m = self.create_member("tear")
    a = self.create_account("tear")
    am = self.create_account_member(a, m)
    ar1 = models.AccountRevision.create_account_revision(a)
    ar2 = models.AccountRevision.create_account_revision(a)
    
    self.assertEqual(ar1, ar2)

  def test_unequal_account_revisions(self):
    m = self.create_member("tear")
    a = self.create_account("tear")
    ar1 = models.AccountRevision.create_account_revision(a)

    am = self.create_account_member(a, m)
    ar2 = models.AccountRevision.create_account_revision(a)
    
    self.assertNotEqual(ar1, ar2)
