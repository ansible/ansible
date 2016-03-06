#!/bin/sh -xe

if [ "${TARGET}" = "sanity" ]; then
    ./test/code-smell/replace-urlopen.sh .
    ./test/code-smell/use-compat-six.sh lib
    ./test/code-smell/boilerplate.sh
    ./test/code-smell/required-and-default-attributes.sh
    if test x"$TOXENV" != x'py24' ; then tox ; fi
    if test x"$TOXENV" = x'py24' ; then python2.4 -V && python2.4 -m compileall -fq -x 'module_utils/(a10|rax|openstack|ec2|gce).py' lib/ansible/module_utils ; fi
else
    docker build --pull=true -t ansible_test/${TARGET} test/utils/docker/${TARGET}
    docker run -d --volume="${PWD}:/root/ansible" ${TARGET_OPTIONS} ansible_test/${TARGET} > /tmp/cid_${TARGET}
    docker exec -ti $(cat /tmp/cid_${TARGET}) /bin/sh -c 'cd /root/ansible; . hacking/env-setup; (cd test/integration; LC_ALL=en_US.utf-8 make)'
    docker kill $(cat /tmp/cid_${TARGET})
fi
