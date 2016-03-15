#!/bin/sh -x

if [ "${TARGET}" = "sanity" ]; then
    ./test/code-smell/replace-urlopen.sh .
    ./test/code-smell/use-compat-six.sh lib
    ./test/code-smell/boilerplate.sh
    ./test/code-smell/required-and-default-attributes.sh
    if test x"$TOXENV" != x'py24' ; then tox ; fi
    if test x"$TOXENV" = x'py24' ; then python2.4 -V && python2.4 -m compileall -fq -x 'module_utils/(a10|rax|openstack|ec2|gce).py' lib/ansible/module_utils ; fi
else
    set -e
    export C_NAME="testAbull_$$_$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)"
    docker run -d --volume="${PWD}:/root/ansible"  --name "${C_NAME}" ${TARGET_OPTIONS} ansible/ansible:${TARGET} > /tmp/cid_${TARGET}
    docker exec -ti $(cat /tmp/cid_${TARGET}) /bin/sh -c "export TEST_FLAGS='${TEST_FLAGS}'; cd /root/ansible; . hacking/env-setup; (cd test/integration; LC_ALL=en_US.utf-8 make)"
    docker kill $(cat /tmp/cid_${TARGET})

    if [ "X${TESTS_KEEP_CONTAINER}" = "X" ]; then
        docker rm "${C_NAME}"
    fi
fi
