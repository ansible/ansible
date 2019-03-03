#!/bin/bash
set -e;
set -u;

START_PORT=$1; # MongoDB Port
REPLSET=$2;    # Replicaset name
NUM=$3;        # Number of mongod processes
AUTH=$4;       # 0 / 1 enable auth

if [ "$AUTH" == "1" ]; then
  echo -e "fd2CUrbXBJpB4rt74A6F" > /root/my.key;
  chmod 600 /root/my.key;
fi;

cd /home/tests
for i in $(seq 1 "$NUM")
do
  mkdir -p mongodb$((START_PORT + $i));
done;

for i in $(seq 1 "$NUM")
do
  if [ "$AUTH" == "0" ]; then
    mongod --shardsvr --smallfiles --storageEngine wiredTiger --wiredTigerEngineConfigString="cache_size=200M" --dbpath mongodb$((START_PORT + $i)) --port $((START_PORT + $i)) --replSet "$REPLSET" --logpath mongodb$((START_PORT + $i))/log.log --fork;
  else
    mongod --shardsvr --smallfiles --storageEngine wiredTiger --wiredTigerEngineConfigString="cache_size=200M" --dbpath mongodb$((START_PORT + $i)) --port $((START_PORT + $i)) --replSet "$REPLSET" --logpath mongodb$((START_PORT + $i))/log.log --fork --auth --keyFile /root/my.key;
  fi;
done;
