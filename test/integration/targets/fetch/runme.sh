#!/usr/bin/env bash

set -eux

function cleanup {
    ansible-playbook -i "${INVENTORY_PATH}" cleanup.yml -e "output_dir=${OUTPUT_DIR}" -b "$@"
    unset ANSIBLE_CACHE_PLUGIN
    unset ANSIBLE_CACHE_PLUGIN_CONNECTION
}

trap 'cleanup "$@"' EXIT

# setup required roles
ln -s ../../setup_remote_tmp_dir roles/setup_remote_tmp_dir

# create vault password files
echo "secret" > vault_pass
echo "secret1" > vault_pass1
cat << "EOF" > ${OUTPUT_DIR}/orig_enc
$ANSIBLE_VAULT;1.2;AES256;vault1
31313538313965306339376134316466333462613034376263643035326338323961303466316434
3738376564383234623363323463646436653962613463370a653136346538653962396433653139
64633565623463633066346330306264626637383763633436316631393361333764393663343065
3761666335336531380a353766633131626538346638663466396161666464306463336536663161
6666
EOF

# run old type role tests
ansible-playbook -i ../../inventory --vault-id default@vault_pass --vault-id vault1@vault_pass1 run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# run same test with become
ansible-playbook -i ../../inventory --vault-id default@vault_pass --vault-id vault1@vault_pass1 run_fetch_tests.yml -e "output_dir=${OUTPUT_DIR}" -b "$@"

# run tests to avoid path injection from slurp when fetch uses become
ansible-playbook -i ../../inventory injection/avoid_slurp_return.yml -e "output_dir=${OUTPUT_DIR}" "$@"

## Test unreadable file with stat. Requires running without become and as a user other than root.
#
# Change the known_hosts file to avoid changing the test environment
export ANSIBLE_CACHE_PLUGIN=jsonfile
export ANSIBLE_CACHE_PLUGIN_CONNECTION="${OUTPUT_DIR}/cache"
# Create a non-root user account and configure SSH acccess for that account
ansible-playbook -i "${INVENTORY_PATH}" setup_unreadable_test.yml -e "output_dir=${OUTPUT_DIR}" "$@"

# Run the tests as the unprivileged user without become to test the use of the stat module from the fetch module
ansible-playbook -i "${INVENTORY_PATH}" test_unreadable_with_stat.yml -e ansible_user=fetcher -e ansible_become=no -e "output_dir=${OUTPUT_DIR}" "$@"
