#!/usr/bin/env bash

set -eux

# test no dupes when dependencies in b and c point to a in roles:
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags inroles | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags acrossroles | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook no_dupes.yml -i ../../inventory --tags intasks | grep -c '"msg": "A"')" = "1" ]

# but still dupe across plays
[ "$(ansible-playbook no_dupes.yml -i ../../inventory | grep -c '"msg": "A"')" = "3" ]

# and don't dedupe before the role successfully completes
[ "$(ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags conditional_skipped | grep -c '"msg": "A"')" = "1" ]
[ "$(ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags conditional_failed | grep -c '"msg": "failed_when task succeeded"')" = "1" ]
[ "$(ANSIBLE_INJECT_INVOCATION=1 ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags unreachable -vvv | grep -c '"data": "reachable"')" = "1" ]
ansible-playbook role_complete.yml -i ../../inventory -i fake, --tags unreachable | grep -e 'ignored=2'

# include/import can execute another instance of role
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags importrole | grep -c '"msg": "A"')" = "2" ]
[ "$(ansible-playbook allowed_dupes.yml -i ../../inventory --tags includerole | grep -c '"msg": "A"')" = "2" ]

[ "$(ansible-playbook dupe_inheritance.yml -i ../../inventory | grep -c '"msg": "abc"')" = "3" ]

# ensure role data is merged correctly
ansible-playbook data_integrity.yml -i ../../inventory "$@"

# ensure role fails when trying to load 'non role' in  _from
test_no_outside=("no_outside.yml" "no_outside_import.yml")
for file in "${test_no_outside[@]}"; do
  ansible-playbook "$file" -i ../../inventory > "${file}_output.log" 2>&1 || true
  if grep "as it is not inside the expected role path" "${file}_output.log" >/dev/null; then
    echo "Test passed for $file (playbook failed with expected output, output not shown)."
  else
    echo "Test failed for $file, expected output from playbook failure is missing, output not shown)."
    exit 1
  fi
done

# ensure subdir contained to role in tasks_from is valid
ansible-playbook test_subdirs.yml -i ../../inventory "$@"

# ensure bare role names are not resolved from the ansible-playbook working directory
target_dir="$(pwd)"
cwd_role_lookup_dir="$(mktemp -d)"
trap 'rm -rf "${cwd_role_lookup_dir}"' EXIT
mkdir -p "${cwd_role_lookup_dir}/cwd/testrole/tasks"
cat > "${cwd_role_lookup_dir}/cwd/testrole/tasks/main.yml" << EOF
- ansible.builtin.debug:
    msg: this should not load from cwd
EOF
(
  cd "${cwd_role_lookup_dir}/cwd"
  ansible-playbook "${target_dir}/cwd_role_lookup.yml" -i "${target_dir}/../../inventory" > "${cwd_role_lookup_dir}/cwd_role_lookup_output.log" 2>&1
) && {
  echo "Test failed for cwd_role_lookup.yml, playbook unexpectedly found role from cwd."
  exit 1
}
grep "role 'testrole' was not found" "${cwd_role_lookup_dir}/cwd_role_lookup_output.log" > /dev/null

# ensure vars scope is correct
ansible-playbook vars_scope.yml -i ../../inventory "$@"

# test nested includes get parent roles greater than a depth of 3
[ "$(ansible-playbook 47023.yml -i ../../inventory | grep '\<\(Default\|Var\)\>' | grep -c 'is defined')" = "2" ]

# ensure import_role called from include_role has the include_role in the dep chain
ansible-playbook role_dep_chain.yml -i ../../inventory "$@"

# global role privacy setting test, set to private, set to not private, default
ANSIBLE_PRIVATE_ROLE_VARS=1 ansible-playbook privacy.yml -e @vars/privacy_vars.yml "$@"
ANSIBLE_PRIVATE_ROLE_VARS=0 ansible-playbook privacy.yml -e @vars/privacy_vars.yml "$@"
ansible-playbook privacy.yml -e @vars/privacy_vars.yml "$@"

for strategy in linear free; do
  [ "$(ANSIBLE_STRATEGY=$strategy ansible-playbook -i testhost, end_role.yml | grep -c CHECKPOINT)" = "2" ]
  [ "$(ANSIBLE_STRATEGY=$strategy ansible-playbook -i host1,host2 end_role_nested.yml | grep -c CHECKPOINT)" = "4" ]
done

[ "$(ansible localhost -m meta -a end_role 2>&1 | grep -c "\[ERROR\]: Cannot execute 'end_role' from outside of a role")" = "1" ]
[ "$(ansible-playbook end_role_handler_error.yml 2>&1 | grep -c "\[ERROR\]: Cannot execute 'end_role' from a handler")" = "1" ]

# include_role should work in rescue, even if error is from magic variable templating
ansible-playbook 75240.yml -i ../../inventory "$@"
