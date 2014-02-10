[ -z "$1" ] && echo "Usage: $0 <username>" && exit
scp $1@mess.mariposa.coop:/tmp/messdev.sql.bz2 ./
bunzip messdev.sql.bz2 | psql
