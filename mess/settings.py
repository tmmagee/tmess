# Django settings for the Mess project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Absolute path to the root of the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# URL of the project.  Leave out a network address to keep links relative.
# Make sure to use a trailing slash.
PROJECT_URL = '/'

ADMINS = (
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3' # 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = PROJECT_ROOT + '/mess.db'             # Or path to database file if using sqlite3.
DATABASE_USER = ''                  # Not used with sqlite3.
DATABASE_PASSWORD = ''        # Not used with sqlite3.
DATABASE_HOST = ''          # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                      # Set to empty string for default. Not used with sqlite3.


TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = PROJECT_URL + 'media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = PROJECT_URL + 'admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4w-cz*to=zc-gjoqtrf=pi2m54i@ghqlnsdq=2mq7e^8fbgh#w'

# Application and model that stores user profiles.
AUTH_PROFILE_MODULE = 'membership.member'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
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
    'mess.autocomplete',
    'mess.accounting',
    'mess.core',
    'mess.forum',
    'mess.membership',
    'mess.reporting',
    'mess.scheduling',
    'mess.events',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
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

