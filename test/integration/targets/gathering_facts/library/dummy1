#!/bin/sh

CANARY="${OUTPUT_DIR}/canary.txt"

echo "$0" >> "${CANARY}"
LINES=0

until test "${LINES}" -gt 2
do
	LINES=`wc -l "${CANARY}" |awk '{print $1}'`
	sleep 1
done

echo '{
    "changed": false,
    "ansible_facts": {
        "dummy": "$0"
    }
}'
