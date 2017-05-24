#!/bin/sh

CMP_USERS=$(grep -rI ' cmp[^a-zA-Z0-9_]' . \
	--exclude-dir .tox \
	| grep -v \
	-e lib/ansible/module_utils/six/_six.py \
	-e test/sanity/code-smell/no-list-cmp.sh
	)

if [ "${CMP_USERS}" ]; then
	echo 'cmp has been removed in python3.  Alternatives:'
	echo '    http://python3porting.com/preparing.html#when-sorting-use-key-instead-of-cmp'
	echo "${CMP_USERS}"
	exit 1
fi
