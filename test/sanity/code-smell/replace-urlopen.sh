#!/bin/sh

urllib_users=$(find . -name '*.py' -exec grep -H urlopen '{}' '+' | grep -v \
    -e '^[^:]*/.tox/' \
    -e '^\./lib/ansible/module_utils/urls.py:' \
    -e '^\./lib/ansible/module_utils/six/__init__.py:' \
    -e '^[^:]*:#'
)

if [ "${urllib_users}" ]; then
    echo "${urllib_users}"
    echo "One or more file(s) listed above use urlopen."
    echo "Use open_url from module_utils instead of urlopen."
    exit 1
fi
