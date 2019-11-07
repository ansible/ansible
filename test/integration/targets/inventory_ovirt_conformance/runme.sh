#!/usr/bin/env bash

set -eux

export PYTHONPATH
PYTHONPATH="$(pwd)/lib:$PYTHONPATH"

if [ -z "${OUTPUT_DIR}" ]; then
    export OUTPUT_DIR=${PWD}
fi

#################################################
#   RUN THE SCRIPT
#################################################

# run the script first
cat << EOF > "$OUTPUT_DIR/ovirt.ini"
[ovirt]
ovirt_url = 'fake'
ovirt_username = 'fake'
ovirt_pasdword = 'fake'
ovirt_cafile = 'fake'
EOF

export OVIRT_INI_PATH=${OUTPUT_DIR}/ovirt.ini
ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i ./ovirt.sh --list --output="$OUTPUT_DIR/script.out"
RC=$?
if [[ $RC != 0 ]]; then
    exit $RC
fi

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=ovirt
export ANSIBLE_INVENTORY="$OUTPUT_DIR/ovirt.yml"

cat << EOF > "$OUTPUT_DIR/ovirt.yml"
plugin: ovirt
ovirt_url: 'fake'
ovirt_username: 'fake'
ovirt_password: 'fake'
ovirt_cafile: 'fake'
ovirt_hostname_preference:
  - name
compose:
   ansible_host: devices["eth0"][0]
keyed_groups:
  - key: tags
    prefix: 'tag'
  - key: cluster
    prefix: 'cluster'
  - key: affinity_groups
    prefix: 'affinity_group'
  - key: affinity_labels
    prefix: 'affinity_label'
  - key: status
    prefix: 'status'
EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i "$OUTPUT_DIR/ovirt.yml" --list --output="$OUTPUT_DIR/plugin.out"

#################################################
#   DIFF THE RESULTS
#################################################
./inventory_diff.py "$OUTPUT_DIR/script.out" "$OUTPUT_DIR/plugin.out"
