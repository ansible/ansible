#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
---
module: ec2_vpc_dhcp_option
short_description: Manages DHCP Options, and can ensure the DHCP options for the given VPC match what's
  requested
description:
  - This module removes, or creates DHCP option sets, and can associate them to a VPC.
    Optionally, a new DHCP Options set can be created that converges a VPC's existing
    DHCP option set with values provided.
    When dhcp_options_id is provided, the module will
    1. remove (with state='absent')
    2. ensure tags are applied (if state='present' and tags are provided
    3. attach it to a VPC (if state='present' and a vpc_id is provided.
    If any of the optional values are missing, they will either be treated
    as a no-op (i.e., inherit what already exists for the VPC)
    To remove existing options while inheriting, supply an empty value
    (e.g. set ntp_servers to [] if you want to remove them from the VPC's options)
    Most of the options should be self-explanatory.
author: "Joel Thompson (@joelthompson)"
version_added: 2.1
options:
  domain_name:
    description:
      - The domain name to set in the DHCP option sets
  dns_servers:
    description:
      - A list of hosts to set the DNS servers for the VPC to. (Should be a
        list of IP addresses rather than host names.)
  ntp_servers:
    description:
      - List of hosts to advertise as NTP servers for the VPC.
  netbios_name_servers:
    description:
      - List of hosts to advertise as NetBIOS servers.
  netbios_node_type:
    description:
      - NetBIOS node type to advertise in the DHCP options.
        The AWS recommendation is to use 2 (when using netbios name services)
        http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_DHCP_Options.html
  vpc_id:
    description:
      - VPC ID to associate with the requested DHCP option set.
        If no vpc id is provided, and no matching option set is found then a new
        DHCP option set is created.
  delete_old:
    description:
      - Whether to delete the old VPC DHCP option set when associating a new one.
        This is primarily useful for debugging/development purposes when you
        want to quickly roll back to the old option set. Note that this setting
        will be ignored, and the old DHCP option set will be preserved, if it
        is in use by any other VPC. (Otherwise, AWS will return an error.)
    type: bool
    default: 'yes'
  inherit_existing:
    description:
      - For any DHCP options not specified in these parameters, whether to
        inherit them from the options set already applied to vpc_id, or to
        reset them to be empty.
    type: bool
    default: 'no'
  tags:
    description:
      - Tags to be applied to a VPC options set if a new one is created, or
        if the resource_id is provided. (options must match)
    aliases: [ 'resource_tags']
    version_added: "2.1"
  dhcp_options_id:
    description:
      - The resource_id of an existing DHCP options set.
        If this is specified, then it will override other settings, except tags
        (which will be updated to match)
    version_added: "2.1"
  state:
    description:
      - create/assign or remove the DHCP options.
        If state is set to absent, then a DHCP options set matched either
        by id, or tags and options will be removed if possible.
    default: present
    choices: [ 'absent', 'present' ]
    version_added: "2.1"
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto
"""

RETURN = """
new_options:
    description: The DHCP options created, associated or found
    returned: when appropriate
    type: dict
    sample:
      domain-name-servers:
        - 10.0.0.1
        - 10.0.1.1
      netbois-name-servers:
        - 10.0.0.1
        - 10.0.1.1
      netbios-node-type: 2
      domain-name: "my.example.com"
dhcp_options_id:
    description: The aws resource id of the primary DCHP options set created, found or removed
    type: string
    returned: when available
changed:
    description: Whether the dhcp options were changed
    type: bool
    returned: always
"""

EXAMPLES = """
# Completely overrides the VPC DHCP options associated with VPC vpc-123456 and deletes any existing
# DHCP option set that may have been attached to that VPC.
- ec2_vpc_dhcp_option:
    domain_name: "foo.example.com"
    region: us-east-1
    dns_servers:
        - 10.0.0.1
        - 10.0.1.1
    ntp_servers:
        - 10.0.0.2
        - 10.0.1.2
    netbios_name_servers:
        - 10.0.0.1
        - 10.0.1.1
    netbios_node_type: 2
    vpc_id: vpc-123456
    delete_old: True
    inherit_existing: False


# Ensure the DHCP option set for the VPC has 10.0.0.4 and 10.0.1.4 as the specified DNS servers, but
# keep any other existing settings. Also, keep the old DHCP option set around.
- ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - "{{groups['dns-primary']}}"
      - "{{groups['dns-secondary']}}"
    vpc_id: vpc-123456
    inherit_existing: True
    delete_old: False


## Create a DHCP option set with 4.4.4.4 and 8.8.8.8 as the specified DNS servers, with tags
## but do not assign to a VPC
- ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - 4.4.4.4
      - 8.8.8.8
    tags:
      Name: google servers
      Environment: Test

## Delete a DHCP options set that matches the tags and options specified
- ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - 4.4.4.4
      - 8.8.8.8
    tags:
      Name: google servers
      Environment: Test
  state: absent

## Associate a DHCP options set with a VPC by ID
- ec2_vpc_dhcp_option:
    region: us-east-1
    dhcp_options_id: dopt-12345678
    vpc_id: vpc-123456

"""

import collections
import traceback
from time import sleep, time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, connect_to_aws, ec2_argument_spec, get_aws_connection_info

if HAS_BOTO:
    import boto.vpc
    import boto.ec2
    from boto.exception import EC2ResponseError


def get_resource_tags(vpc_conn, resource_id):
    return dict((t.name, t.value) for t in vpc_conn.get_all_tags(filters={'resource-id': resource_id}))


def retry_not_found(to_call, *args, **kwargs):
    start_time = time()
    while time() < start_time + 300:
        try:
            return to_call(*args, **kwargs)
        except EC2ResponseError as e:
            if e.error_code == 'InvalidDhcpOptionID.NotFound':
                sleep(3)
                continue
            raise e


def ensure_tags(module, vpc_conn, resource_id, tags, add_only, check_mode):
    try:
        cur_tags = get_resource_tags(vpc_conn, resource_id)
        if tags == cur_tags:
            return {'changed': False, 'tags': cur_tags}

        to_delete = dict((k, cur_tags[k]) for k in cur_tags if k not in tags)
        if to_delete and not add_only:
            retry_not_found(vpc_conn.delete_tags, resource_id, to_delete, dry_run=check_mode)

        to_add = dict((k, tags[k]) for k in tags if k not in cur_tags)
        if to_add:
            retry_not_found(vpc_conn.create_tags, resource_id, to_add, dry_run=check_mode)

        latest_tags = get_resource_tags(vpc_conn, resource_id)
        return {'changed': True, 'tags': latest_tags}
    except EC2ResponseError as e:
        module.fail_json(msg="Failed to modify tags: %s" % e.message, exception=traceback.format_exc())


def fetch_dhcp_options_for_vpc(vpc_conn, vpc_id):
    """
    Returns the DHCP options object currently associated with the requested VPC ID using the VPC
    connection variable.
    """
    vpcs = vpc_conn.get_all_vpcs(vpc_ids=[vpc_id])
    if len(vpcs) != 1 or vpcs[0].dhcp_options_id == "default":
        return None
    dhcp_options = vpc_conn.get_all_dhcp_options(dhcp_options_ids=[vpcs[0].dhcp_options_id])
    if len(dhcp_options) != 1:
        return None
    return dhcp_options[0]


def match_dhcp_options(vpc_conn, tags=None, options=None):
    """
    Finds a DHCP Options object that optionally matches the tags and options provided
    """
    dhcp_options = vpc_conn.get_all_dhcp_options()
    for dopts in dhcp_options:
        if (not tags) or get_resource_tags(vpc_conn, dopts.id) == tags:
            if (not options) or dopts.options == options:
                return(True, dopts)
    return(False, None)


def remove_dhcp_options_by_id(vpc_conn, dhcp_options_id):
    associations = vpc_conn.get_all_vpcs(filters={'dhcpOptionsId': dhcp_options_id})
    if len(associations) > 0:
        return False
    else:
        vpc_conn.delete_dhcp_options(dhcp_options_id)
        return True


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        dhcp_options_id=dict(type='str', default=None),
        domain_name=dict(type='str', default=None),
        dns_servers=dict(type='list', default=None),
        ntp_servers=dict(type='list', default=None),
        netbios_name_servers=dict(type='list', default=None),
        netbios_node_type=dict(type='int', default=None),
        vpc_id=dict(type='str', default=None),
        delete_old=dict(type='bool', default=True),
        inherit_existing=dict(type='bool', default=False),
        tags=dict(type='dict', default=None, aliases=['resource_tags']),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ec2_vpc_dhcp_options':
        module.deprecate("The 'ec2_vpc_dhcp_options' module has been renamed "
                         "'ec2_vpc_dhcp_option' (option is no longer plural)",
                         version=2.8)

    params = module.params
    found = False
    changed = False
    new_options = collections.defaultdict(lambda: None)

    if not HAS_BOTO:
        module.fail_json(msg='boto is required for this module')

    region, ec2_url, boto_params = get_aws_connection_info(module)
    connection = connect_to_aws(boto.vpc, region, **boto_params)

    existing_options = None

    # First check if we were given a dhcp_options_id
    if not params['dhcp_options_id']:
        # No, so create new_options from the parameters
        if params['dns_servers'] is not None:
            new_options['domain-name-servers'] = params['dns_servers']
        if params['netbios_name_servers'] is not None:
            new_options['netbios-name-servers'] = params['netbios_name_servers']
        if params['ntp_servers'] is not None:
            new_options['ntp-servers'] = params['ntp_servers']
        if params['domain_name'] is not None:
            # needs to be a list for comparison with boto objects later
            new_options['domain-name'] = [params['domain_name']]
        if params['netbios_node_type'] is not None:
            # needs to be a list for comparison with boto objects later
            new_options['netbios-node-type'] = [str(params['netbios_node_type'])]
        # If we were given a vpc_id then we need to look at the options on that
        if params['vpc_id']:
            existing_options = fetch_dhcp_options_for_vpc(connection, params['vpc_id'])
            # if we've been asked to inherit existing options, do that now
            if params['inherit_existing']:
                if existing_options:
                    for option in ['domain-name-servers', 'netbios-name-servers', 'ntp-servers', 'domain-name', 'netbios-node-type']:
                        if existing_options.options.get(option) and new_options[option] != [] and (not new_options[option] or [''] == new_options[option]):
                            new_options[option] = existing_options.options.get(option)

            # Do the vpc's dhcp options already match what we're asked for? if so we are done
            if existing_options and new_options == existing_options.options:
                module.exit_json(changed=changed, new_options=new_options, dhcp_options_id=existing_options.id)

        # If no vpc_id was given, or the options don't match then look for an existing set using tags
        found, dhcp_option = match_dhcp_options(connection, params['tags'], new_options)

    # Now let's cover the case where there are existing options that we were told about by id
    # If a dhcp_options_id was supplied we don't look at options inside, just set tags (if given)
    else:
        supplied_options = connection.get_all_dhcp_options(filters={'dhcp-options-id': params['dhcp_options_id']})
        if len(supplied_options) != 1:
            if params['state'] != 'absent':
                module.fail_json(msg=" a dhcp_options_id was supplied, but does not exist")
        else:
            found = True
            dhcp_option = supplied_options[0]
            if params['state'] != 'absent' and params['tags']:
                ensure_tags(module, connection, dhcp_option.id, params['tags'], False, module.check_mode)

    # Now we have the dhcp options set, let's do the necessary

    # if we found options we were asked to remove then try to do so
    if params['state'] == 'absent':
        if not module.check_mode:
            if found:
                changed = remove_dhcp_options_by_id(connection, dhcp_option.id)
        module.exit_json(changed=changed, new_options={})

    # otherwise if we haven't found the required options we have something to do
    elif not module.check_mode and not found:

        # create some dhcp options if we weren't able to use existing ones
        if not found:
            # Convert netbios-node-type and domain-name back to strings
            if new_options['netbios-node-type']:
                new_options['netbios-node-type'] = new_options['netbios-node-type'][0]
            if new_options['domain-name']:
                new_options['domain-name'] = new_options['domain-name'][0]

            # create the new dhcp options set requested
            dhcp_option = connection.create_dhcp_options(
                new_options['domain-name'],
                new_options['domain-name-servers'],
                new_options['ntp-servers'],
                new_options['netbios-name-servers'],
                new_options['netbios-node-type'])

            # wait for dhcp option to be accessible
            found_dhcp_opt = False
            start_time = time()
            try:
                found_dhcp_opt = retry_not_found(connection.get_all_dhcp_options, dhcp_options_ids=[dhcp_option.id])
            except EC2ResponseError as e:
                module.fail_json(msg="Failed to describe DHCP options", exception=traceback.format_exc)
            if not found_dhcp_opt:
                module.fail_json(msg="Failed to wait for {0} to be available.".format(dhcp_option.id))

            changed = True
            if params['tags']:
                ensure_tags(module, connection, dhcp_option.id, params['tags'], False, module.check_mode)

    # If we were given a vpc_id, then attach the options we now have to that before we finish
    if params['vpc_id'] and not module.check_mode:
        changed = True
        connection.associate_dhcp_options(dhcp_option.id, params['vpc_id'])
        # and remove old ones if that was requested
        if params['delete_old'] and existing_options:
            remove_dhcp_options_by_id(connection, existing_options.id)

    module.exit_json(changed=changed, new_options=new_options, dhcp_options_id=dhcp_option.id)


if __name__ == "__main__":
    main()
