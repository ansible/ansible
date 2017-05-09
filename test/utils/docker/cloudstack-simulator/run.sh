#!/bin/bash
until nc -z localhost 8096; do
    echo "waiting for port 8096..."
    sleep 3
done

sleep 3
if [ ! -e /var/www/html/admin.json ]
then
  python /opt/cloudstack/tools/marvin/marvin/deployDataCenter.py -i /opt/zones.cfg
  export CLOUDSTACK_ENDPOINT=http://127.0.0.1:8096
  export CLOUDSTACK_KEY=""
  export CLOUDSTACK_SECRET=""
  cs listUsers account=admin | jq .user[0] > /var/www/html/admin.json
fi
