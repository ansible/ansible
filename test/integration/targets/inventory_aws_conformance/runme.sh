#!/usr/bin/env bash

set -eux

source virtualenv.sh

pip install "python-dateutil>=2.1,<2.7.0" jmespath "Jinja2==2.10" "MarkupSafe==1.1.1"

# create boto3 symlinks
ln -s "$(pwd)/lib/boto" "$(pwd)/lib/boto3"
ln -s "$(pwd)/lib/boto" "$(pwd)/lib/botocore"

# override boto's import path(s)
export PYTHONPATH
PYTHONPATH="$(pwd)/lib:$PYTHONPATH"

#################################################
#   RUN THE SCRIPT
#################################################

# run the script first
cat << EOF > "$OUTPUT_DIR/ec2.ini"
[ec2]
regions = us-east-1
cache_path = $(pwd)/.cache
cache_max_age = 0
group_by_tag_none = False

[credentials]
aws_access_key_id = FOO
aws_secret_acccess_key = BAR
EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i ./ec2.sh --list --output="$OUTPUT_DIR/script.out"
RC=$?
if [[ $RC != 0 ]]; then
    exit $RC
fi

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=aws_ec2
export ANSIBLE_INVENTORY=test.aws_ec2.yml
export AWS_ACCESS_KEY_ID=FOO
export AWS_SECRET_ACCESS_KEY=BAR
export ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never

cat << EOF > "$OUTPUT_DIR/test.aws_ec2.yml"
plugin: aws_ec2
cache: False
use_contrib_script_compatible_sanitization: True
strict: True
regions:
    - us-east-1
hostnames:
  - network-interface.addresses.association.public-ip
  - dns-name
filters:
  instance-state-name: running
compose:
  # vars that don't exist anymore in any meaningful way
  ec2_item: undefined | default("")
  ec2_monitoring: undefined | default("")
  ec2_previous_state: undefined | default("")
  ec2_previous_state_code: undefined | default(0)
  ec2__in_monitoring_element: undefined | default(false)
  # the following three will be accessible again after #53645
  ec2_requester_id: undefined | default("")
  ec2_eventsSet: undefined | default("")
  ec2_persistent: undefined | default(false)

  # vars that change
  ansible_host: public_ip_address
  ec2_block_devices: dict(block_device_mappings | map(attribute='device_name') | map('basename') | list | zip(block_device_mappings | map(attribute='ebs.volume_id') | list))
  ec2_dns_name: public_dns_name
  ec2_group_name: placement['group_name']
  ec2_id: instance_id
  ec2_instance_profile: iam_instance_profile | default("")
  ec2_ip_address: public_ip_address
  ec2_kernel: kernel_id | default("")
  ec2_monitored:  monitoring['state'] in ['enabled', 'pending']
  ec2_monitoring_state: monitoring['state']
  ec2_account_id: owner_id
  ec2_placement: placement['availability_zone']
  ec2_ramdisk: ramdisk_id | default("")
  ec2_reason: state_transition_reason
  ec2_security_group_ids: security_groups | map(attribute='group_id') | list | sort | join(',')
  ec2_security_group_names: security_groups | map(attribute='group_name') | list | sort | join(',')
  ec2_state: state['name']
  ec2_state_code: state['code']
  ec2_state_reason: state_reason['message'] if state_reason is defined else ""
  ec2_sourceDestCheck: source_dest_check | lower | string  # butchered snake_case case not a typo.

  # vars that just need ec2_ prefix
  ec2_ami_launch_index: ami_launch_index | string
  ec2_architecture: architecture
  ec2_client_token: client_token
  ec2_ebs_optimized: ebs_optimized
  ec2_hypervisor: hypervisor
  ec2_image_id: image_id
  ec2_instance_type: instance_type
  ec2_key_name: key_name
  ec2_launch_time: 'launch_time | regex_replace(" ", "T") | regex_replace("(\+)(\d\d):(\d)(\d)$", ".\g<2>\g<3>Z")'
  ec2_platform: platform | default("")
  ec2_private_dns_name: private_dns_name
  ec2_private_ip_address: private_ip_address
  ec2_public_dns_name: public_dns_name
  ec2_region: placement['region']
  ec2_root_device_name: root_device_name
  ec2_root_device_type: root_device_type
  ec2_spot_instance_request_id: spot_instance_request_id | default("")
  ec2_subnet_id: subnet_id
  ec2_virtualization_type: virtualization_type
  ec2_vpc_id: vpc_id
  tags: dict(tags.keys() | map('regex_replace', '[^A-Za-z0-9\_]', '_') | list | zip(tags.values() | list))

keyed_groups:
  - key: '"ec2"'
    separator: ""
  - key: 'instance_id'
    separator: ""
  - key: tags
    prefix: tag
  - key: key_name | regex_replace('-', '_')
    prefix: key
  - key: placement['region']
    separator: ""
  - key: placement['availability_zone']
    separator: ""
  - key: platform | default('undefined')
    prefix: platform
  - key: vpc_id | regex_replace('-', '_')
    prefix: vpc_id
  - key: instance_type
    prefix: type
  - key: "image_id | regex_replace('-', '_')"
    separator: ""
  - key: security_groups | map(attribute='group_name') | map("regex_replace", "-", "_") | list
    prefix: security_group
EOF

ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i "$OUTPUT_DIR/test.aws_ec2.yml" --list --output="$OUTPUT_DIR/plugin.out"

#################################################
#   DIFF THE RESULTS
#################################################

./inventory_diff.py "$OUTPUT_DIR/script.out" "$OUTPUT_DIR/plugin.out"
