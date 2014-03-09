#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y gunicorn nginx postgresql python-dateutil python-feedparser

echo 'Installing Django...'
cd /tmp
wget -nv https://www.djangoproject.com/m/releases/1.4/Django-1.4.10.tar.gz
tar xzf Django-1.4.10.tar.gz
cd Django-1.4.10
python setup.py -q install
cd ..
rm -rf Django-1.4.10*

echo 'Configuring nginx...'
cat > /etc/nginx/sites-available/mess << 'EOF'
server {
  listen 80;
  server_name mess.mariposa.coop;
  client_max_body_size 10m;
  client_body_buffer_size 128k;
    
  keepalive_timeout 1000;

  location /media {
    alias /vagrant/mess/media;
  }

  location / {
      # an HTTP header important enough to have its own Wikipedia entry:
      #   http://en.wikipedia.org/wiki/X-Forwarded-For
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

      # pass the Host: header from the client right along so redirects
      # can be set properly within the Rack application
      proxy_set_header Host $host;

      # we don't want nginx trying to do something clever with
      # redirects, we set the Host: header above already.
      proxy_redirect off;

      proxy_pass http://127.0.0.1:8000;
  }
}
EOF
/etc/init.d/nginx restart

echo 'Configuring gunicorn...'
cat > /etc/gunicorn.d/mess << 'EOF'
CONFIG = {
  'mode': 'django',
  'working_dir': '/vagrant/mess/',
  'user': 'www-data',
  'group': 'www-data',
  'args': (
    '--bind=127.0.0.1:8000',
    '--worker-class=egg:gunicorn#sync',
    '--timeout=1000',
    # For dev. See http://stackoverflow.com/questions/12773763/gunicorn-autoreload-on-source-change
    '--max-requests=1',
    '--workers=1',
  ),
}
EOF
/etc/init.d/gunicorn restart

echo 'Creating MESS DB...'
sudo -u postgres createuser -S -D -R mess
sudo -u postgres createdb -O mess mess

echo 'Writing local settings for MESS...'
cat > /vagrant/mess/settings_local.py << 'EOF'
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Dev', 'dev@localhost'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mess',
        'USER': 'mess',
        'PASSWORD': 'mess',
        'HOST': 'localhost',
        'PORT': '',
    }
}

SECRET_KEY = 'secret'

DEFAULT_FROM_EMAIL = 'do-not-reply@localhost'
SERVER_EMAIL = 'hq@localhost'

MARIPOSA_IPS = ('192.168.48.24')

GOTOPHPBB_SECRET='phpbbsecret'
GOTOIS4C_SECRET='is4secret'
IS4C_SECRET='is4secret'
EOF

echo 'MESS box provisioned!'
