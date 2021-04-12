#!/usr/bin/env bash

set -eux

export ANSIBLE_INVENTORY_ENABLED=toml

# A few things to make it easier to grep against adhoc
export ANSIBLE_LOAD_CALLBACK_PLUGINS=True
export ANSIBLE_STDOUT_CALLBACK=oneline

adhoc="$(ansible -i test1.toml -m ping --connection=local -e ansible_python_interpreter="{{ ansible_playbook_python }}" all -v)"

for i in $(seq -f '%03g' 1 4); do
    grep -qE "local${i} \| SUCCESS.*\"ping\": \"pong\"" <<< "$adhoc"
done

bad_ext="$(ansible -i foo.nottoml -m ping all -vvv 2>&1)"
grep -q "toml declined parsing" <<< "$bad_ext"

doesnotexist="$(ansible -i doesnotexist.toml -m ping all -vvv 2>&1)"
grep -q "toml declined parsing" <<< "$doesnotexist"

empty="$(ansible -i empty.toml -m ping all -vvv 2>&1)"
grep -q "Failed to parse.*" <<< "$empty"
grep -q "Parsed empty TOML file" <<< "$empty"

plugin="$(ansible -i plugin.toml -m ping all -vvv 2>&1)"
grep -q "Failed to parse.*" <<< "$plugin"
grep -q "Plugin configuration TOML file" <<< "$plugin"
grep -q "not TOML inventory" <<< "$plugin"

malformed="$(ansible -i malformed.toml -m ping all -vvv 2>&1)"
grep -q "Failed to parse.*" <<< "$malformed"
grep -q "name found without" <<< "$malformed"

invalid_group="$(ansible -i invalid_group.toml -m ping all -vvv 2>&1)"
grep -q "Skipping 'invalid_group'" <<< "$invalid_group"

unexp_vars="$(ansible -i invalid_group_vars.toml -m ping all -vvv 2>&1)"
grep -q "Invalid \"vars\" entry for \"mygroup\"" <<< "$unexp_vars"

unexp_children="$(ansible -i invalid_group_children.toml -m ping all -vvv 2>&1)"
grep -q "Invalid \"children\" entry for \"mygroup\"" <<< "$unexp_children"

unexp_key="$(ansible -i invalid_group_key.toml -m ping all -vvv 2>&1)"
grep -q "Skipping unexpected key \"something\"" <<< "$unexp_key"

invalid_hosts="$(ansible -i invalid_group_hosts.toml -m ping all -vvv 2>&1)"
grep -q "Invalid \"hosts\" entry for \"mygroup\" group" <<< "$invalid_hosts"

ansible-inventory -i children.toml --graph 2>&1 | diff -u - children_graph.txt

# needs #74234
bash missing_toml_venv.sh
bash old_toml_venv.sh
