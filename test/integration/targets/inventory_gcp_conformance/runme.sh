#!/usr/bin/env bash

set -eux

# set the output dir
if [ -z "${OUTPUT_DIR+null}" ]; then
    export OUTPUT_DIR=${PWD}
fi

echo "PWD: $PWD"
export PYTHONPATH="${PWD}/lib:$PYTHONPATH"

# Create fake credentials
cat << EOF > "$OUTPUT_DIR/gcp_credentials.json"
{
  "type": "service_account",
  "project_id": "foo",
  "private_key_id": "FOO",
  "private_key": "BAR",
  "client_email": "FOOBAR@foo.iam.gserviceaccount.com",
  "client_id": "BAZ",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "MEH"
}

EOF

#################################################
#   RUN THE SCRIPT
#################################################

# run the script first
cat << EOF > "$OUTPUT_DIR/gce.ini"
[gce]
gce_service_account_pem_file_path = $OUTPUT_DIR/gcp_credentials.json
gce_service_account_email_address = FOOBAR@foo.iam.gserviceaccount.com
gce_project_id = foo
gce_zone = us-east1-d

EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i ./gce.sh --list --output="${OUTPUT_DIR}/script.out"
RC=$?
if [[ $RC != 0 ]]; then
    exit $RC
fi

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
cat << EOF > "$OUTPUT_DIR/test.gcp.yml"
plugin: gcp_compute
projects:
  - foo
auth_kind: serviceaccount
service_account_file: $OUTPUT_DIR/gcp_credentials.json
compose:
  ansible_ssh_host: networkInterfaces[0]['accessConfigs'][0]['natIP']
  gce_description: description if description else None
  gce_id: id
  gce_image: image
  gce_machine_type: machineType
  gce_metadata: metadata.get("items", []) | items2dict(key_name="key", value_name="value")
  gce_name: name
  gce_network: networkInterfaces[0]['network']['name']
  gce_private_ip: networkInterfaces[0]['networkIP']
  gce_public_ip: networkInterfaces[0]['accessConfigs'][0]['natIP']
  gce_status: status
  gce_subnetwork: networkInterfaces[0]['subnetwork']['name']
  gce_tags: tags.get("items", [])
  gce_zone: zone
hostnames:
- name
- public_ip
- private_ip
keyed_groups:
- key: gce_subnetwork
  prefix: network
- key: gce_private_ip
  prefix: ''
  separator: ''
- key: gce_public_ip
  prefix: ''
  separator: ''
- key: machineType
  prefix: ''
  separator: ''
- key: zone
  prefix: ''
  separator: ''
- key: gce_tags
  prefix: tag
- key: image
  prefix: ''
  separator: ''
- key: status | lower
  prefix: status
zones:
  - us-east1-d
use_contrib_script_compatible_sanitization: true
retrieve_image_info: true
EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i "${OUTPUT_DIR}/test.gcp.yml" --list --output="${OUTPUT_DIR}/plugin.out"

#################################################
#   DIFF THE RESULTS
#################################################

./inventory_diff.py "${OUTPUT_DIR}/script.out" "${OUTPUT_DIR}/plugin.out"
