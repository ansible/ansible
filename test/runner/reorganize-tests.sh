#!/usr/bin/env bash

set -eu

source_root=$(python -c "from os import path; print(path.abspath(path.join(path.dirname('$0'), '..', '..')))")

cd "${source_root}"

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
