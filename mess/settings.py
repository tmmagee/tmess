# Django settings for the Mess project.

import os

DEBUG = True
MAINTENANCE = False
TEMPLATE_DEBUG = DEBUG

# Absolute path to the root of the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# URL of the project.  Leave out a network address to keep links relative.
# Make sure to use a trailing slash.
PROJECT_URL = '/'

ADMINS = (
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',             # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_ROOT + 'mess.db', # Or path to database file if using sqlite3.
        'USER': '',                       # Not used with sqlite3.
        'PASSWORD': '',                   # Not used with sqlite3.
        'HOST': '',                       # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                       # Set to empty string for default. Not used with sqlite3.
    }
}
#DATABASE_ENGINE = 'sqlite3' # 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = PROJECT_ROOT + '/mess.db'             # Or path to database file if using sqlite3.
#DATABASE_USER = ''                  # Not used with sqlite3.
#DATABASE_PASSWORD = ''        # Not used with sqlite3.
#DATABASE_HOST = ''          # Set to empty string for localhost. Not used with sqlite3.
#DATABASE_PORT = ''                      # Set to empty string for default. Not used with sqlite3.


TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/usr/share/nginx/www/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'hyhb9iu_)5q5-54_oz2e)=ihs7!^kix)^g^+9q4!3yl_@&amp;a@&amp;6'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tom.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'tom.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = PROJECT_URL + 'media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4w-cz*to=zc-gjoqtrf=pi2m54i@ghqlnsdq=2mq7e^8fbgh#w'

# Application and model that stores user profiles.
AUTH_PROFILE_MODULE = 'membership.member'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mess.core.middleware.UserPassesTestMiddleware',
)

ROOT_URLCONF = 'mess.urls'

LOCATION = 'Cashier'
MARIPOSA_IPS = ('127.0.0.1')

TEMPLATE_DIRS = (
    PROJECT_ROOT + '/templates',
)

FIXTURE_DIRS = (
    PROJECT_ROOT + '/fixtures',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.markup',
    'django.contrib.staticfiles',
    'mess.autocomplete',
    'mess.accounting',
    'mess.core',
    'mess.forum',
    'mess.membership',
    'mess.reporting',
    'mess.scheduling',
    'mess.events',
    'mess.revision',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'mess.core.context_processors.role_permissions',
    'mess.core.context_processors.location',
)

LOGIN_URL = PROJECT_URL
LOGIN_REDIRECT_URL = PROJECT_URL

CACHE_BACKEND = 'locmem://'

# Default to clearing everything at browser close.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Settings for UserPassesTestMiddleware

# UserPassesTestMiddleware setting.  This means the whole site is locked down 
# to staff only.  Put an auth decorator such as login_required on a view 
# function to allow non-staff access.
USER_PASSES_TEST_URLS = (
    (r'^/$', None), 
    (r'^/maintenance/$', None), 
    (r'^/login/$', None),
    (r'^/logout/$', None),
    (r'^/media/', None),
    (r'^/passwordreset/', None),
    (r'^/accounting/listen_to_paypal', None),
    (r'^/is4c/', None),
    (r'^/membership/signup/member/$', None),
    (r'^/membership/signup/orientation/$', None),
    (r'', lambda u: u.is_staff),
)

AUTHENTICATION_BACKENDS = (
    'mess.core.backends.ModelBackend',
)

# Uncomment for email testing
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

## mess project constants below ##

GOTOFORUM_SECRET = 'The real secret should be specified under settings_local.py'
IS4C_SECRET = 'fakesecret'

try:
    from settings_local import *
except ImportError:
    pass

