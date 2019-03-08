#!/usr/bin/env bash

set -eux

# set the output dir
if [ -z ${OUTPUT_DIR+null} ]; then
    export OUTPUT_DIR=$(pwd)
fi

#################################################
#   RUN THE SCRIPT
#################################################

# run the script first
cat << EOF > $OUTPUT_DIR/ec2.ini
[ec2]
regions = us-east-1
cache_path = $(pwd)/.cache
cache_max_age = 0
group_by_tag_none = False

[credentials]
aws_access_key_id = FOO
aws_secret_acccess_key = BAR
EOF

rm -f script.out
./ec2.sh | tee -a $OUTPUT_DIR/script.out
#./ec2.sh 
RC=$?
if [[ $RC != 0 ]]; then
    exit $RC
fi
#rm -f $OUTPUT_DIR/ec2.ini
#rm -f $OUTPUT_DIR/ec2.py
rm -rf .cache

#exit 0

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=aws_ec2
export ANSIBLE_INVENTORY=test.aws_ec2.yml
export AWS_ACCESS_KEY_ID=FOO
export AWS_SECRET_ACCESS_KEY=BAR

cat << EOF > $OUTPUT_DIR/test.aws_ec2.yml
plugin: aws_ec2
cache: False
regions:
    - us-east-1
hostnames:
  - dns-name
compose:
  # vars that don't exist
  ansible_host: public_dns_name
  ec2_item: backwardscompat | default("")  # boto anomaly, always appears to be u'\n', don't see a reason to keep it around
  ec2_monitoring: backwardscompat | default("") # boto anomaly, always appears to be u'\n', don't see a reason to keep it around
  ec2_previous_state: backwardscompat | default("")  # This is only returned with boto3 when starting, stopping, and terminating instances, not applicable
  ec2_previous_state_code: backwardscompat | default(0)  # This is only returned with boto3 when starting, stopping, and terminating instances
  ec2__in_monitoring_element: backwardscompat | default(false)  # double underscore not a typo. Trying to figure out wth this was.
  ec2_requester_id: backwardscompat | default("") # FIXME not an attribute returned anymore on instances in boto3, will need code change
  ec2_account_id: backwardscompat | default("") # FIXME not an attribute returned anymore on instances in boto3, will need code change
  ec2_eventsSet: backwardscompat | default("")  # FIXME would need to add a describe_instance_status API call for instances to be able to add an events hostvar
  ec2_persistent: backwardscompat | default(false)  # FIXME would need to add a describe_spot_instance_requests API call for any instances that have the SpotInstanceRequestId variable

  # vars that change
  ec2_block_devices: dict(block_device_mappings | map(attribute='device_name') | list | zip(block_device_mappings | map(attribute='ebs.volume_id') | list))
  ec2_dns_name: public_dns_name
  ec2_group_name: placement.group_name
  ec2_id: instance_id
  ec2_instance_profile: iam_instance_profile | default("")
  ec2_ip_address: public_ip_address
  ec2_kernel: kernel_id | default("")
  ec2_monitored:  monitoring.state in ['enabled', 'pending']
  ec2_monitoring_state: monitoring.state
  ec2_owner_id: account_id
  ec2_placement: placement.availability_zone
  ec2_ramdisk: ramdisk_id | default("")
  ec2_reason: state_transition_reason
  ec2_security_group_ids: security_groups | map(attribute='group_id') | list |  join(',')
  ec2_security_group_names: security_groups | map(attribute='name') | list |  join(',')
  ec2_state: state.name
  ec2_state_code: state.code
  ec2_state_reason: state_reason.message if state_reason is defined else ""
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
  ec2_region: placement.region
  ec2_root_device_name: root_device_name
  ec2_root_device_type: root_device_type
  ec2_spot_instance_request_id: spot_instance_request_id
  ec2_subnet_id: subnet_id
  ec2_virtualization_type: virtualization_type
  ec2_vpc_id: vpc_id

keyed_groups:
  - key: '"ec2"'
    separator: ""
  - key: 'instance_id'
    separator: ""
  - key: tags
    prefix: tag
  - key: key_name
    prefix: key
  - key: placement.region
    separator: ""
  - key: placement.availability_zone
    separator: ""
  - key: platform
    prefix: platform
  - key: vpc_id
    prefix: vpc_id
  - key: instance_type
    prefix: type
  - key: image_id
    separator: ""
  - key: 'security_groups | json_query("[].name")'
    prefix: security_group
EOF

# override boto's import path(s)
echo "PWD: $(pwd)"
export PYTHONPATH=$(pwd)/lib:$PYTHONPATH

rm -f $OUTPUT_DIR/plugin.out
#ansible-inventory -i $OUTPUT_DIR/test.aws_ec2.yml --list | tee -a $OUTPUT_DIR/plugin.out
ANSIBLE_JINJA2_NATIVE=1 ansible-inventory -vvvv -i $OUTPUT_DIR/test.aws_ec2.yml --list --output=$OUTPUT_DIR/plugin.out
rm -f $OUTPUT_DIR/aws_ec2.yml

#################################################
#   DIFF THE RESULTS
#################################################

./inventory_diff.py $OUTPUT_DIR/script.out $OUTPUT_DIR/plugin.out
