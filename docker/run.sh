#docker run -P -v $PWD/mess:/usr/local/src/mess -t gsf747/mess gunicorn mess.wsgi:application -b 0.0.0.0.:8000 --max-requests 1
#docker run -i -P -v $PWD/mess:/usr/local/src/mess -t gsf747/mess bash
docker run -name=postgresql -d -v /tmp/postgresql:/data -t gsf747/postgresql
docker run -name=mess -d -P -link postgresql:db -v $PWD/mess:/usr/local/src/mess -t gsf747/mess
