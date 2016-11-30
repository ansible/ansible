#!/usr/bin/env bash

set -eu

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '..', '..')))")

cd "${source_root}"

# Convert existing compile skip files to match the unified repository layout.

mkdir -p test/compile

rm -f test/compile/*.txt

for type in core extras; do
    sed "s|^|/lib/ansible/modules/${type}|" \
        < "lib/ansible/modules/${type}/test/utils/shippable/sanity-skip-python24.txt" \
        >> "test/compile/python2.4-skip.txt"
done

# Existing skip files are only for modules.
# Add missing skip entries for core code.

cat << EOF >> test/compile/python2.4-skip.txt
/lib/ansible/modules/__init__.py
/lib/ansible/module_utils/a10.py
/lib/ansible/module_utils/rax.py
/lib/ansible/module_utils/openstack.py
/lib/ansible/module_utils/cloud.py
/lib/ansible/module_utils/ec2.py
/lib/ansible/module_utils/gce.py
/lib/ansible/module_utils/lxd.py
/lib/ansible/module_utils/docker_common.py
/lib/ansible/module_utils/azure_rm_common.py
/lib/ansible/module_utils/vca.py
/lib/ansible/module_utils/vmware.py
/lib/ansible/module_utils/gcp.py
/lib/ansible/module_utils/gcdns.py
/lib/ansible/vars/
/lib/ansible/utils/
/lib/ansible/template/
/lib/ansible/plugins/
/lib/ansible/playbook/
/lib/ansible/parsing/
/lib/ansible/inventory/
/lib/ansible/galaxy/
/lib/ansible/executor/
/lib/ansible/errors/
/lib/ansible/compat/
/lib/ansible/config/
/lib/ansible/cli/
/lib/ansible/constants.py
/lib/ansible/release.py
/lib/ansible/__init__.py
/hacking/
/contrib/
/docsite/
/test/
EOF

cat << EOF >> test/compile/python2.6-skip.txt
/contrib/inventory/vagrant.py
/hacking/dump_playbook_attributes.py
EOF

cat << EOF >> test/compile/python3.5-skip.txt
/test/samples/multi.py
/examples/scripts/uptime.py
EOF

for path in test/compile/*.txt; do
    sort -o "${path}" "${path}"
done

# Not all scripts pass shellcheck yet.

mkdir -p test/sanity/shellcheck

cat << EOF > test/sanity/shellcheck/skip.txt
test/sanity/code-smell/boilerplate.sh
EOF

sort -o test/sanity/shellcheck/skip.txt test/sanity/shellcheck/skip.txt

# Add skip list for code-smell scripts.
# These scripts don't pass, so we can't run them in CI.

cat << EOF > test/sanity/code-smell/skip.txt
inappropriately-private.sh
EOF

# Add skip list for validate-modules.
# Some of these exclusions are temporary, others belong in validate-modules.
cat << EOF > test/sanity/validate-modules/skip.txt
lib/ansible/modules/core/utilities/logic/async_status.py
lib/ansible/modules/core/utilities/helper/_fireball.py
lib/ansible/modules/core/utilities/helper/_accelerate.py
lib/ansible/modules/core/test
lib/ansible/modules/core/.github
lib/ansible/modules/extras/test
lib/ansible/modules/extras/.github
EOF

# Remove existing aliases from previous script runs.
rm -f test/integration/targets/*/aliases

# Map destructive/ targets to integration tests.
targets=$(grep 'role:' "test/integration/destructive.yml" \
    | sed 's/^.* role: //; s/[ ,].*$//;')

for target in ${targets}; do
    alias='destructive'
    echo "target: ${target}, alias: ${alias}"
    echo "${alias}" >> "test/integration/targets/${target}/aliases"
done

# Map destructive/non_destructive targets to posix groups for integration tests.
# This will allow re-balancing of posix tests on Shippable independently of destructive/non_destructive targets.
for type in destructive non_destructive; do
    targets=$(grep 'role:' "test/integration/${type}.yml" \
        | sed 's/^.* role: //; s/[ ,].*$//;')

    if [ "${type}" = "destructive" ]; then
        group="posix/ci/group1"
    else
        group="posix/ci/group2"
    fi

    for target in ${targets}; do
        echo "target: ${target}, group: ${group}"
        echo "${group}" >> "test/integration/targets/${target}/aliases"
    done
done

# Add aliases to integration tests.
targets=$(grep 'role:' test/integration/{destructive,non_destructive}.yml \
    | sed 's/^.* role: //; s/[ ,].*$//;')

for target in ${targets}; do
    aliases=$(grep -h "role: *${target}[ ,]" test/integration/{destructive,non_destructive}.yml \
        | sed 's/when:[^,]*//;' \
        | sed 's/^.*tags:[ []*//g; s/[]}].*$//g; s/ //g; s/,/ /g; s/test_//g;')

    for alias in ${aliases}; do
        if [ "${target}" != "${alias}" ]; then
            # convert needs_ prefixed aliases to groups
            alias="${alias//needs_/needs\/}"

            echo "target: ${target}, alias: ${alias}"
            echo "${alias}" >> "test/integration/targets/${target}/aliases"
        fi
    done
done

# Map test_win_group* targets to windows groups for integration tests.
for type in test_win_group1 test_win_group2 test_win_group3; do
    targets=$(grep 'role:' "test/integration/${type}.yml" \
        | sed 's/^.* role: //; s/[ ,].*$//;')

    group=$(echo "${type}" | sed 's/^test_win_/windows_/; s/_/\/ci\//;')

    for target in ${targets}; do
        echo "target: ${target}, group: ${group}"
        echo "${group}" >> "test/integration/targets/${target}/aliases"
    done
done

# Add additional windows tests to appropriate groups.
echo 'windows/ci/group2' >> test/integration/targets/binary_modules_winrm/aliases
echo 'windows/ci/group3' >> test/integration/targets/connection_winrm/aliases

# Add posix/ci/group3 for posix tests which are not already grouped for ci.
group="posix/ci/group3"
for target in test/integration/targets/*; do
    target=$(basename "${target}")
    if [[ "${target}" =~ (setup|prepare)_ ]]; then
        continue
    fi
    if [ -f "test/integration/targets/${target}/test.sh" ]; then
        continue
    fi
    if [ -f "test/integration/targets/${target}/aliases" ]; then
        if grep -q -P "^(windows|posix)/" "test/integration/targets/${target}/aliases"; then
            continue
        fi
    fi
    if [[ "${target}" =~ _ ]]; then
        prefix="${target//_*/}"
        if grep -q --line-regex "${prefix}" test/integration/target-prefixes.*; then
            continue
        fi
    fi
    echo "target: ${target}, group: ${group}"
    echo "${group}" >> "test/integration/targets/${target}/aliases"
done

# Add skip aliases for python3.
sed 's/^test_//' test/utils/shippable/python3-test-tag-blacklist.txt | while IFS= read -r target; do
    echo "skip/python3" >> "test/integration/targets/${target}/aliases"
done

# Add skip aliases for tests which don't pass yet on osx/freebsd.
for target in service postgresql mysql_db mysql_user mysql_variables uri get_url async_extra_data; do
    echo "skip/osx" >> "test/integration/targets/${target}/aliases"
    echo "skip/freebsd" >> "test/integration/targets/${target}/aliases"
done

# Add skip aliases for tests which don't pass yet on osx.
for target in gathering_facts iterators git; do
    echo "skip/osx" >> "test/integration/targets/${target}/aliases"
done

# Add needs/root entries as required.
for target in connection_chroot authorized_key copy template unarchive; do
    echo "needs/root" >> "test/integration/targets/${target}/aliases"
done

# Add needs/ssh entries as required.
for target in async_extra_data connection_ssh connection_paramiko_ssh; do
    echo "needs/ssh" >> "test/integration/targets/${target}/aliases"
done

# Add missing alias for windows async_status.
echo "async_status" >> test/integration/targets/win_async_wrapper/aliases

# Remove connection tests from CI groups which aren't supported yet.
for connection in docker jail libvirt_lxc lxc lxd; do
    target="connection_${connection}"
    sed -i '/^posix\/ci\/.*$/d' "test/integration/targets/${target}/aliases"
done

# Sort aliases.
for file in test/integration/targets/*/aliases; do
    sort -o "${file}" "${file}"
done
