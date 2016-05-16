#!/bin/sh

set -e
set -u
set -x

LINKS="--link=httptester:ansible.http.tests --link=httptester:sni1.ansible.http.tests --link=httptester:sni2.ansible.http.tests --link=httptester:fail.ansible.http.tests"

if [ "${TARGET}" = "sanity" ]; then
    ./test/code-smell/replace-urlopen.sh .
    ./test/code-smell/use-compat-six.sh lib
    ./test/code-smell/boilerplate.sh
    ./test/code-smell/required-and-default-attributes.sh
    if test x"$TOXENV" != x'py24' ; then tox ; fi
    if test x"$TOXENV" = x'py24' ; then python2.4 -V && python2.4 -m compileall -fq -x 'module_utils/(a10|rax|openstack|ec2|gce|docker_common|azure_rm_common|vca|vmware).py' lib/ansible/module_utils ; fi
else
    if [ ! -e /tmp/cid_httptester ]; then
        docker pull sivel/httptester
        docker run -d --name=httptester sivel/httptester > /tmp/cid_httptester
    fi
    export C_NAME="testAbull_$$_$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)"
    docker pull ansible/ansible:${TARGET}
    docker run -d --volume="${PWD}:/root/ansible:Z" $LINKS --name "${C_NAME}" ${TARGET_OPTIONS:=''} ansible/ansible:${TARGET} > /tmp/cid_${TARGET}
    docker exec -ti $(cat /tmp/cid_${TARGET}) /bin/sh -c "export TEST_FLAGS='${TEST_FLAGS:-''}'; cd /root/ansible; . hacking/env-setup; (cd test/integration; LC_ALL=en_US.utf-8 make ${MAKE_TARGET:-})"
    docker kill $(cat /tmp/cid_${TARGET})

    if [ "X${TESTS_KEEP_CONTAINER:-""}" = "X" ]; then
        docker rm -vf "${C_NAME}"
    fi
fi
