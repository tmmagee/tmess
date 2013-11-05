from django.db.models.signals import post_save
from django.dispatch import receiver
from mess.revision import models
from mess.membership import models as m_models

from django.db.models import fields

def member_revision_has_changes(revision):
  most_recent_revision = models.MemberRevision.objects.filter(member_id=revision.member_id).order_by('-timestamp')[1]

  return revision != most_recent_revision

def account_revision_has_changes(revision):
  most_recent_revision = models.AccountRevision.objects.filter(account_id=revision.account_id).order_by('-timestamp')[1]
  return revision != most_recent_revision

@receiver(post_save, sender=m_models.Member)
def record_member_revision(signal, sender, instance, created, raw, using, **kwargs):
  member_revision = models.MemberRevision.create_member_revision(member=instance)

  if not created and not member_revision_has_changes(member_revision):
    member_revision.delete()

@receiver(post_save, sender=m_models.Account)
def record_account_revision(signal, sender, instance, created, raw, using, **kwargs):

  account_revision = models.AccountRevision.create_account_revision(account=instance)

  if not created and not account_revision_has_changes(account_revision):
    account_revision.delete()
