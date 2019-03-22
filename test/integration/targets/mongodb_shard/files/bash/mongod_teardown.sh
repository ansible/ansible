#!/bin/bash

killall mongod || true
rm -rf /home/tests/mongodb* || true;
rm -f /tmp/mongo*.sock || true;
sleep 10;
