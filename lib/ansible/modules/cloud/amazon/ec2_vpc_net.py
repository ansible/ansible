#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2_vpc_net
short_description: Configure AWS virtual private clouds
description:
    - Create, modify, and terminate AWS virtual private clouds.
version_added: "2.0"
author:
  - Jonathan Davila (@defionscode)
  - Sloane Hertel (@s-hertel)
options:
  name:
    description:
      - The name to give your VPC. This is used in combination with C(cidr_block) to determine if a VPC already exists.
    required: yes
  cidr_block:
    description:
      - The primary CIDR of the VPC. After 2.5 a list of CIDRs can be provided. The first in the list will be used as the primary CIDR
        and is used in conjunction with the C(name) to ensure idempotence.
    required: yes
  purge_cidrs:
    description:
      - Remove CIDRs that are associated with the VPC and are not specified in C(cidr_block).
    default: no
    type: bool
    version_added: '2.5'
  tenancy:
    description:
      - Whether to be default or dedicated tenancy. This cannot be changed after the VPC has been created.
    default: default
    choices: [ 'default', 'dedicated' ]
  dns_support:
    description:
      - Whether to enable AWS DNS support.
    default: yes
    type: bool
  dns_hostnames:
    description:
      - Whether to enable AWS hostname support.
    default: yes
    type: bool
  dhcp_opts_id:
    description:
      - the id of the DHCP options to use for this vpc
  tags:
    description:
      - The tags you want attached to the VPC. This is independent of the name value, note if you pass a 'Name' key it would override the Name of
        the VPC if it's different.
    aliases: [ 'resource_tags' ]
  state:
    description:
      - The state of the VPC. Either absent or present.
    default: present
    choices: [ 'present', 'absent' ]
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block. Specify this as true if you want
        duplicate VPCs created.
    default: false
requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: create a VPC with dedicated tenancy and a couple of tags
  ec2_vpc_net:
    name: Module_dev2
    cidr_block: 10.10.0.0/16
    region: us-east-1
    tags:
      module: ec2_vpc_net
      this: works
    tenancy: dedicated
'''

RETURN = '''
vpc:
  description: info about the VPC that was created or deleted
  returned: always
  type: complex
  contains:
    cidr_block:
      description: The CIDR of the VPC
      returned: always
      type: string
      sample: 10.0.0.0/16
    cidr_block_association_set:
      description: IPv4 CIDR blocks associated with the VPC
      returned: success
      type: list
      sample:
        "cidr_block_association_set": [
            {
                "association_id": "vpc-cidr-assoc-97aeeefd",
                "cidr_block": "20.0.0.0/24",
                "cidr_block_state": {
                    "state": "associated"
                }
            }
        ]
    classic_link_enabled:
      description: indicates whether ClassicLink is enabled
      returned: always
      type: NoneType
      sample: null
    dhcp_options_id:
      description: the id of the DHCP options assocaited with this VPC
      returned: always
      type: string
      sample: dopt-0fb8bd6b
    id:
      description: VPC resource id
      returned: always
      type: string
      sample: vpc-c2e00da5
    instance_tenancy:
      description: indicates whether VPC uses default or dedicated tenancy
      returned: always
      type: string
      sample: default
    is_default:
      description: indicates whether this is the default VPC
      returned: always
      type: bool
      sample: false
    state:
      description: state of the VPC
      returned: always
      type: string
      sample: available
    tags:
      description: tags attached to the VPC, includes name
      returned: always
      type: complex
      contains:
        Name:
          description: name tag for the VPC
          returned: always
          type: string
          sample: pk_vpc4
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from time import sleep, time
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry, camel_dict_to_snake_dict, compare_aws_tags,
                                      ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict)
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.module_utils.network.common.utils import to_subnet


def vpc_exists(module, vpc, name, cidr_block, multi):
    """Returns None or a vpc object depending on the existence of a VPC. When supplied
    with a CIDR, it will check for matching tags to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return None.
    """
    try:
        matching_vpcs = vpc.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [name]}, {'Name': 'cidr-block', 'Values': cidr_block}])['Vpcs']
        # If an exact matching using a list of CIDRs isn't found, check for a match with the first CIDR as is documented for C(cidr_block)
        if not matching_vpcs:
            matching_vpcs = vpc.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [name]}, {'Name': 'cidr-block', 'Values': [cidr_block[0]]}])['Vpcs']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    if multi:
        return None
    elif len(matching_vpcs) == 1:
        return matching_vpcs[0]['VpcId']
    elif len(matching_vpcs) > 1:
        module.fail_json(msg='Currently there are %d VPCs that have the same name and '
                             'CIDR block you specified. If you would like to create '
                             'the VPC anyway please pass True to the multi_ok param.' % len(matching_vpcs))
    return None


@AWSRetry.backoff(delay=3, tries=8, catch_extra_error_codes=['InvalidVpcID.NotFound'])
def get_classic_link_with_backoff(connection, vpc_id):
    try:
        return connection.describe_vpc_classic_link(VpcIds=[vpc_id])['Vpcs'][0].get('ClassicLinkEnabled')
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Message"] == "The functionality you requested is not available in this region.":
            return False
        else:
            raise


def get_vpc(module, connection, vpc_id):
    # wait for vpc to be available
    try:
        connection.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC {0} to be available.".format(vpc_id))

    try:
        vpc_obj = AWSRetry.backoff(
            delay=3, tries=8,
            catch_extra_error_codes=['InvalidVpcID.NotFound'],
        )(connection.describe_vpcs)(VpcIds=[vpc_id])['Vpcs'][0]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")
    try:
        vpc_obj['ClassicLinkEnabled'] = get_classic_link_with_backoff(connection, vpc_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe VPCs")

    return vpc_obj


def update_vpc_tags(connection, module, vpc_id, tags, name):
    if tags is None:
        tags = dict()

    tags.update({'Name': name})
    tags = dict((k, to_native(v)) for k, v in tags.items())
    try:
        current_tags = dict((t['Key'], t['Value']) for t in connection.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}])['Tags'])
        tags_to_update, dummy = compare_aws_tags(current_tags, tags, False)
        if tags_to_update:
            if not module.check_mode:
                tags = ansible_dict_to_boto3_tag_list(tags_to_update)
                vpc_obj = AWSRetry.backoff(
                    delay=1, tries=5,
                    catch_extra_error_codes=['InvalidVpcID.NotFound'],
                )(connection.create_tags)(Resources=[vpc_id], Tags=tags)

                # Wait for tags to be updated
                expected_tags = boto3_tag_list_to_ansible_dict(tags)
                filters = [{'Name': 'tag:{0}'.format(key), 'Values': [value]} for key, value in expected_tags.items()]
                connection.get_waiter('vpc_available').wait(VpcIds=[vpc_id], Filters=filters)

            return True
        else:
            return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update tags")


def update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
    if vpc_obj['DhcpOptionsId'] != dhcp_id:
        if not module.check_mode:
            try:
                connection.associate_dhcp_options(DhcpOptionsId=dhcp_id, VpcId=vpc_obj['VpcId'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to associate DhcpOptionsId {0}".format(dhcp_id))

            try:
                # Wait for DhcpOptionsId to be updated
                filters = [{'Name': 'dhcp-options-id', 'Values': [dhcp_id]}]
                connection.get_waiter('vpc_available').wait(VpcIds=[vpc_obj['VpcId']], Filters=filters)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json(msg="Failed to wait for DhcpOptionsId to be updated")

        return True
    else:
        return False


def create_vpc(connection, module, cidr_block, tenancy):
    try:
        if not module.check_mode:
            vpc_obj = connection.create_vpc(CidrBlock=cidr_block, InstanceTenancy=tenancy)
        else:
            module.exit_json(changed=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to create the VPC")

    # wait for vpc to exist
    try:
        connection.get_waiter('vpc_exists').wait(VpcIds=[vpc_obj['Vpc']['VpcId']])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to wait for VPC {0} to be created.".format(vpc_obj['Vpc']['VpcId']))

    return vpc_obj['Vpc']['VpcId']


def wait_for_vpc_attribute(connection, module, vpc_id, attribute, expected_value):
    start_time = time()
    updated = False
    while time() < start_time + 300:
        current_value = connection.describe_vpc_attribute(
            Attribute=attribute,
            VpcId=vpc_id
        )['{0}{1}'.format(attribute[0].upper(), attribute[1:])]['Value']
        if current_value != expected_value:
            sleep(3)
        else:
            updated = True
            break
    if not updated:
        module.fail_json(msg="Failed to wait for {0} to be updated".format(attribute))


def get_cidr_network_bits(module, cidr_block):
    fixed_cidrs = []
    for cidr in cidr_block:
        split_addr = cidr.split('/')
        if len(split_addr) == 2:
            # this_ip is a IPv4 CIDR that may or may not have host bits set
            # Get the network bits.
            valid_cidr = to_subnet(split_addr[0], split_addr[1])
            if cidr != valid_cidr:
                module.warn("One of your CIDR addresses ({0}) has host bits set. To get rid of this warning, "
                            "check the network mask and make sure that only network bits are set: {1}.".format(cidr, valid_cidr))
            fixed_cidrs.append(valid_cidr)
        else:
            # let AWS handle invalid CIDRs
            fixed_cidrs.append(cidr)
    return fixed_cidrs


def main():
    argument_spec = dict(
        name=dict(required=True),
        cidr_block=dict(type='list', required=True),
        tenancy=dict(choices=['default', 'dedicated'], default='default'),
        dns_support=dict(type='bool', default=True),
        dns_hostnames=dict(type='bool', default=True),
        dhcp_opts_id=dict(),
        tags=dict(type='dict', aliases=['resource_tags']),
        state=dict(choices=['present', 'absent'], default='present'),
        multi_ok=dict(type='bool', default=False),
        purge_cidrs=dict(type='bool', default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    name = module.params.get('name')
    cidr_block = get_cidr_network_bits(module, module.params.get('cidr_block'))
    purge_cidrs = module.params.get('purge_cidrs')
    tenancy = module.params.get('tenancy')
    dns_support = module.params.get('dns_support')
    dns_hostnames = module.params.get('dns_hostnames')
    dhcp_id = module.params.get('dhcp_opts_id')
    tags = module.params.get('tags')
    state = module.params.get('state')
    multi = module.params.get('multi_ok')

    changed = False

    connection = module.client(
        'ec2',
        retry_decorator=AWSRetry.jittered_backoff(
            retries=8, delay=3, catch_extra_error_codes=['InvalidVpcID.NotFound']
        )
    )

    if dns_hostnames and not dns_support:
        module.fail_json(msg='In order to enable DNS Hostnames you must also enable DNS support')

    if state == 'present':

        # Check if VPC exists
        vpc_id = vpc_exists(module, connection, name, cidr_block, multi)

        if vpc_id is None:
            vpc_id = create_vpc(connection, module, cidr_block[0], tenancy)
            changed = True

        vpc_obj = get_vpc(module, connection, vpc_id)

        associated_cidrs = dict((cidr['CidrBlock'], cidr['AssociationId']) for cidr in vpc_obj.get('CidrBlockAssociationSet', [])
                                if cidr['CidrBlockState']['State'] != 'disassociated')
        to_add = [cidr for cidr in cidr_block if cidr not in associated_cidrs]
        to_remove = [associated_cidrs[cidr] for cidr in associated_cidrs if cidr not in cidr_block]
        expected_cidrs = [cidr for cidr in associated_cidrs if associated_cidrs[cidr] not in to_remove] + to_add

        if len(cidr_block) > 1:
            for cidr in to_add:
                changed = True
                connection.associate_vpc_cidr_block(CidrBlock=cidr, VpcId=vpc_id)

        if purge_cidrs:
            for association_id in to_remove:
                changed = True
                try:
                    connection.disassociate_vpc_cidr_block(AssociationId=association_id)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, "Unable to disassociate {0}. You must detach or delete all gateways and resources that "
                                         "are associated with the CIDR block before you can disassociate it.".format(association_id))

        if dhcp_id is not None:
            try:
                if update_dhcp_opts(connection, module, vpc_obj, dhcp_id):
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, "Failed to update DHCP options")

        if tags is not None or name is not None:
            try:
                if update_vpc_tags(connection, module, vpc_id, tags, name):
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to update tags")

        current_dns_enabled = connection.describe_vpc_attribute(Attribute='enableDnsSupport', VpcId=vpc_id, aws_retry=True)['EnableDnsSupport']['Value']
        current_dns_hostnames = connection.describe_vpc_attribute(Attribute='enableDnsHostnames', VpcId=vpc_id, aws_retry=True)['EnableDnsHostnames']['Value']
        if current_dns_enabled != dns_support:
            changed = True
            if not module.check_mode:
                try:
                    connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': dns_support})
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, "Failed to update enabled dns support attribute")
        if current_dns_hostnames != dns_hostnames:
            changed = True
            if not module.check_mode:
                try:
                    connection.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': dns_hostnames})
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, "Failed to update enabled dns hostnames attribute")

        # wait for associated cidrs to match
        if to_add or to_remove:
            try:
                connection.get_waiter('vpc_available').wait(
                    VpcIds=[vpc_id],
                    Filters=[{'Name': 'cidr-block-association.cidr-block', 'Values': expected_cidrs}]
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, "Failed to wait for CIDRs to update")

        # try to wait for enableDnsSupport and enableDnsHostnames to match
        wait_for_vpc_attribute(connection, module, vpc_id, 'enableDnsSupport', dns_support)
        wait_for_vpc_attribute(connection, module, vpc_id, 'enableDnsHostnames', dns_hostnames)

        final_state = camel_dict_to_snake_dict(get_vpc(module, connection, vpc_id))
        final_state['tags'] = boto3_tag_list_to_ansible_dict(final_state.get('tags', []))
        final_state['id'] = final_state.pop('vpc_id')

        module.exit_json(changed=changed, vpc=final_state)

    elif state == 'absent':

        # Check if VPC exists
        vpc_id = vpc_exists(module, connection, name, cidr_block, multi)

        if vpc_id is not None:
            try:
                if not module.check_mode:
                    connection.delete_vpc(VpcId=vpc_id)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete VPC {0} You may want to use the ec2_vpc_subnet, ec2_vpc_igw, "
                                     "and/or ec2_vpc_route_table modules to ensure the other components are absent.".format(vpc_id))

        module.exit_json(changed=changed, vpc={})


if __name__ == '__main__':
    main()
