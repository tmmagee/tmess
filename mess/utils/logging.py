from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode

FLAG_MAP = {
    'add': ADDITION,
    'edit': CHANGE,
    'delete': DELETION,
}

# logs any action on a database record to django's admin interface
#
# HOW IT WORKS: i
# - If the caller supplied a change_message, that is the 
#   only entry logged.
# - If the record is new or deleted, the entry simply states as much
# - If the record has been updated, this function cycles through the 
#   record's old values and logs a message for each value that was changed
def log(request, obj, action_flag, change_message='', old_values=None):

    if change_message:
	    LogEntry.objects.log_action(
	        user_id = request.user.pk,
	        content_type_id = ContentType.objects.get_for_model(obj).pk,
	        object_id = obj.pk,
	        object_repr = obj._meta.app_label + "." + obj._meta.object_name,
	        action_flag = FLAG_MAP[action_flag],
	        change_message = change_message,
	    )
    elif FLAG_MAP[action_flag] == ADDITION:
	    LogEntry.objects.log_action(
	        user_id = request.user.pk,
	        content_type_id = ContentType.objects.get_for_model(obj).pk,
	        object_id = obj.pk,
	        object_repr = obj._meta.app_label + "." + obj._meta.object_name,
	        action_flag = FLAG_MAP[action_flag],
	        change_message = "New record added"
	    )
    elif old_values and FLAG_MAP[action_flag] == CHANGE:
        for key in old_values:
            if not key.startswith('_') and \
                    old_values[key] != obj.__dict__[key]:

                change_message = 'Changed %s: "%s" to "%s"' % (key, old_values[key], obj.__dict__[key])
	            
                LogEntry.objects.log_action(
	                user_id = request.user.pk,
	                content_type_id = ContentType.objects.get_for_model(obj).pk,
	                object_id = obj.pk,
	                object_repr = obj._meta.app_label + "." + obj._meta.object_name,
	                action_flag = FLAG_MAP[action_flag],
	                change_message = change_message,
	            )
    elif FLAG_MAP[action_flag] == DELETION:
	    LogEntry.objects.log_action(
	        user_id = request.user.pk,
	        content_type_id = ContentType.objects.get_for_model(obj).pk,
	        object_id = obj.pk,
	        object_repr = obj._meta.app_label + "." + obj._meta.object_name,
	        action_flag = FLAG_MAP[action_flag],
	        change_message = "Record deleted"
	    )
