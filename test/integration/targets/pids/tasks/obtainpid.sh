#!/usr/bin/env bash
$1 100 & 
echo $! > /root/ansible/test/integration/targets/pids/tasks/obtainpid.txt
