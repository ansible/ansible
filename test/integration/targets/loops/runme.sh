#!/usr/bin/env bash

set -eu

ansible-playbook playbook.yml -i ../../inventory "$@"

rm -f out.txt && touch out.txt

python ../test_utils/scripts/timeout.py -- 10 'ansible-playbook test_loop_item_display.yml "$@" >> out.txt' &

echo "waiting for first loop result..."
# wait up to 2s for first loop result to appear
python ../test_utils/scripts/timeout.py -- 2 tail -f out.txt | grep item=0 -m 1 || (echo "failed to get first loop result in time" && false)

echo "checking for absence of second loop result..."
# fail if the second loop result appeared too early
grep item=2 out.txt && (echo "found the second loop result early, failing" && false)

echo "waiting for second loop result..."
# wait up to 3s for second loop result to appear
python ../test_utils/scripts/timeout.py -- 3 tail -f out.txt | grep item=2 -m 1 || (echo "failed to get second loop result in time" && false)

echo "success"
