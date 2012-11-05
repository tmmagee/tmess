from django import forms
from mess.forum import models

class AddPostForm(forms.Form):
    forum = forms.ModelChoiceField(models.Forum.objects.all(),
            widget=forms.HiddenInput())
    subject = forms.CharField(widget=forms.TextInput(attrs={'size':50}))
    body = forms.CharField(widget=forms.Textarea(attrs={'cols':80}))
    attachment = forms.FileField(required=False)
    
    # hide subject and attachment if this is a reply
    def __init__(self, *args, **kwargs):
        super(AddPostForm, self).__init__(*args, **kwargs)
        if self.initial.get('subject') or self.data.get('subject'):
            self.fields['subject'].widget = forms.HiddenInput()
            self.fields['attachment'].widget = forms.HiddenInput()

    def save(self, author):

        attachment = self.cleaned_data.get('attachment')

        ''' We only allow pdf attachments for now '''
        if attachment and attachment.content_type == 'application/pdf':
          attachment = models.Attachment.objects.create(name=attachment, file_upload=attachment)
        else:
          attachment = None

        self.instance = models.Post.objects.create(
                        forum=self.cleaned_data.get('forum'),
                        author=author,
                        subject=self.cleaned_data.get('subject'),
                        body=self.cleaned_data.get('body'))

        if attachment:
          self.instance.attachments.add(attachment)
