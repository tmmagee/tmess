from django.contrib import admin

from mess.forum import models

class PostAdmin(admin.ModelAdmin):
  ordering=('-timestamp',)

admin.site.register(models.Forum)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Attachment)
