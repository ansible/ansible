#!/usr/bin/python
# Copyright 2013 Google Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_net
version_added: "1.5"
short_description: create/destroy GCE networks and subnets
description:
    - This module can create and destroy Google Compute Engine networks and
      subnets U(https://cloud.google.com/compute/docs/vpc/).
      Installation/configuration instructions for the gce_* modules can
      be found at U(https://docs.ansible.com/ansible/guide_gce.html).
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 1.0.0"
author:
    - "Eric Johnson (@erjohnso) <erjohnso@google.com>"
    - "Tom Melendez (@supertom) <supertom@google.com>"
    - "Nikolaos Kakouros (@tterranigma) <tterranigma@gmail.com>"
options:
    name:
        description:
            - The name of the network.
        required: true
    mode:
        version_added: "2.2"
        description:
            - Network mode for Google Cloud.
            - I(legacy) indicates a network with an IP address range.
            - I(auto) automatically generates subnetworks in different regions.
            - I(custom) uses networks to group subnets of user specified IP address ranges.
            - See U(https://cloud.google.com/compute/docs/networking#network_types) for more information.
        choices: ["legacy", "auto", "custom"]
        default: "legacy"
    legacy_range:
        version_added: "2.4"
        description:
          - The IPv4 address range in CIDR notation for the legacy.
          - Allowed and required when I(mode=legacy)
    subnets:
        version_added: "2.4"
        description:
            - A list of the subnets to create on the network.
            - The list is a list of dictionaries, each of which has 3 required options and one optional.
            - Required options are I(name), I(region) and I(range) (in cidr notation)
            - Optional option is I(description)
            - See the examples on how to use them.
            - Google Cloud identifies subnets based on the (subnet-name, region) tuple.
    subnet_policy:
        version_added: "2.4"
        description:
            - If I(ignore_strays) and I(state=present), the defined I(subnets) will be created as normal.
            - If I(include_strays) and I(state=present), prior to creating the I(subnets), ansible
              will also check if there are other, "stray" subnets on GCE that are not
              specified in the I(subnets) option.
            - If I(ignore_strays) and I(state=absent), ansible will check if there are "stray" subnets on the
              network. If there are, the task will fail and no changes will be performed.
            - If I(include_strays) and I(state=absent), all subnets on the network will be destroyed
              including those that are not specified in I(subnets).
            - To have full control of what exists on GCE, set I(subnet_policy=include_strays).
        choices: ["ignore_strays", "include_strays"]
    state:
        description:
            - Desired state of the network.
            - When deleting the network (changing from I(present) to I(absent)), the subnets will also be deleted.
            - See also the I(subnet_policy).
            - It is not possible to delete subnets that contain instances.
        default: "present"
        choices: ["present", "absent"]
notes:
    - Google Cloud supports only IPv4 networks.
    - The ip ranges used should be in cidr notation.
    - Subnets in custom mode are not allowed to have overlapping cidr ranges.
      Eg, a subnet with I(range=10.0.0.0/20) and one with I(range=10.0.0.0/16) will trigger an errror.
    - Subnets that carry instances cannot be destroyed unless the instances are destroye first. Use M(gce) module for that.
    - Although this module supports check mode, there is one case when check_mode will report inconsistent results.
      This is when you try to destroy a subnet that contains instances. This cannot be checked before trying and it is a
      limitation of the Google Cloud API
'''

EXAMPLES = '''
# Create a 'legacy' Network
- name: Create Legacy Network
  gce_net:
    name: legacynet
    mode: legacy
    legacy_range: '10.24.17.0/24'
    state: present

# Create an 'auto' Network
- name: Create Auto Network
  gce_net:
    name: autonet
    mode: auto

# Create a 'custom' Network
- name: Create Custom Network
  gce_net:
    name: customnet
    mode: custom
    subnets:
      - name: subnet1
        range: 10.0.0.0/20
        region: europe-west1
        description: Sample description
      - name: subnet2
        range: 10.1.0.0/20
        region: us-central1
        description: Another description
'''

RETURN = '''
name:
    description: name of the network
    returned: always
    type: string
    sample: "my-network"

mode:
    description: the mode of the network
    returned: always
    type: string
    sample: "custom"

legacy_range:
    description: IPv4 range of the legacy network
    returned: when I(mode=legacy)
    type: string
    sample: "10.0.0.0/16"

gateway_ip:
    description: the gateway IP of the legacy network
    returned: when I(mode=legacy)
    type: string
    sample: 10.240.0.1

subnets:
    description:
        - The subnets that were specified (see the I(subnets) option for available keys).
        - In addition, the following extra keys will also be returned: creation_time, gateway_address, self_link
        - See other return values with the same name for more information
    returned: when I(mode=custom)
    type: dict
    sample: "my-subnetwork"

subnet_policy:
    description: the policy when creating subnets (see the I(subnet_policy) option for more details)
    returned: when I(mode=custom)
    type: string
    sample: ignore_strays

state:
    description: state of the item operated on
    returned: always
    type: string
    sample: "present"

self_link:
    description: firewall resource uri on GCE
    returned: always
    type: string
    sample: https://www.googleapis.com/compute/v1/projects/myproject/global/networks/mynet

creation_time:
    description: network creation timestamp
    returned: always
    type: string
    sample: "2017-06-28T10:59:59.698-07:00"
'''

################################################################################
# Imports
################################################################################

try:
    from libcloud import __version__ as LIBCLOUD_VERSION
    from libcloud.compute.types import Provider
    from libcloud.common.google import ResourceNotFoundError, InvalidRequestError, \
        ResourceInUseError

    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

# module specific imports
from distutils.version import LooseVersion
import re

from sys import version_info

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect


################################################################################
# Constants
################################################################################

# subnet methods were introduced in 1.0.0
MINIMUM_LIBCLOUD_VERSION = '1.0.0'

try:
    PROVIDER = Provider.GCE
except NameError:
    # libcloud may not have been successfully imported. In that case, execution
    # will stop after check_libs() has been called.
    pass


################################################################################
# Functions
################################################################################

def check_libs(module):
    # Apache libcloud needs to be installed and at least the minimum version.
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )
    elif LooseVersion(LIBCLOUD_VERSION) < MINIMUM_LIBCLOUD_VERSION:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )


def check_subnet_spec(module):
    # this will check if all the required subnet option are set on each subnet
    for subnet in module.params['subnets']:
        try:
            subnet['name']
            subnet['region']
            subnet['range']
        except KeyError as e:
            module.fail_json(
                msg="mode is custom but the following option for subnet '%s' is missing: %s" % (subnet['name'], str(e)),
                changed=False
            )


def additional_constraint_checks(module):
    msg = ''

    # AnsibleModule doesn't provide a way to apply constraints in sub-dicts in argument_spec
    if module.params['mode'] == 'custom':
        check_subnet_spec(module)

    if module.params['mode'] == 'auto':
        if module.params['legacy_range'] is not None:
            msg = "mode is auto but legacy_range is defined."

        if module.params['subnets'] is not None:
            msg = "mode is auto but subnet definitions are given."

        if module.params['subnet_policy'] is not None:
            msg = "mode is auto but subnet_policy is defined."

    if module.params['mode'] == 'legacy':
        if module.params['subnets'] is not None:
            msg = "mode is legacy but subnet definitions are given."

    if msg:
        module.fail_json(msg=msg, changed=False)


# The next 4 functions are custom. We did not import ipaddr or ipadress or other
# libraries because some are unmaintained, python3 incompatible or buggy.
def get_subnet_id(cidr):
    address, mask = cidr.split('/')

    # convert netmask to host mask
    netmask = (0xffffffff >> (32 - int(mask))) << (32 - int(mask))

    # convert address to binary
    address = address.split('.')
    for index, part in enumerate(address):
        address[index] = "{0:08b}".format(int(part))
    address = ''.join(address)

    network_id = int(address, 2) & int(netmask)
    return network_id


def get_host_id(cidr):
    address, mask = cidr.split('/')

    # convert netmask to host mask
    hostmask = (0xffffffff >> (int(mask)))

    # convert address to binary
    address = address.split('.')
    for index, part in enumerate(address):
        address[index] = "{0:08b}".format(int(part))
    address = ''.join(address)
    host_id = int(address, 2) & int(hostmask)

    return host_id


def check_subnet_id(cidr):
    # cidr range regexp. Using a regexp to avoid loading extra python dependencies (ipaddr)
    cidr_regexp = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$"

    # first do a simple value check
    matches = re.match(cidr_regexp, cidr)
    if not matches:
        return 1

    # now check that there is no host id
    host_id = get_host_id(cidr)

    if host_id:
        return 2

    return 0


def check_overlapping_subnets(subnet1, subnet2):
    subnet_id1 = get_subnet_id(subnet1)
    subnet_id2 = get_subnet_id(subnet2)

    overlap = subnet_id1 & subnet_id2

    #  if overlap == subnet_id1 or overlap == subnet_id2:
        #  return 1

    return 0


def check_parameters(module):
    # All the below checks are performed to allow check_mode to give reliable results.
    # Otherwise, we could handle the exceptions raised by libcloud and skip doing
    # duplicate work here.
    msg = ''

    # Starts with lowercase letter, contains only lowercase letters, nubmers, hyphens,
    # cannot be empty, cannot end with hyphen. Taken directly for GCE error responses.
    name_regexp = r"(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)"

    # check the firewall rule name.
    matches = re.match(name_regexp, module.params['name'])
    if not matches:
        msg = "Network name must start with a lowercase letter, can contain only lowercase letters, " \
            + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check legacy_range
    if module.params['legacy_range'] is not None:
        result = check_subnet_id(module.params['legacy_range'])
        if result == 1:
            msg = "legacy_range must be a valid cidr range, '%s' is invalid" % module.params['legacy_range']
        if result == 2:
            msg = "legacy_range must not have a host id part"

    if msg:
        module.fail_json(msg=msg, changed=False)


def check_subnet_parameters(module, gce_connection):
    msg = ''

    # Starts with lowercase letter, contains only lowercase letters, nubmers, hyphens,
    # cannot be empty, cannot end with hyphen. Taken directly for GCE error responses.
    name_regexp = r"^(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)$"

    # cidr range regexp. Using a regexp to avoid loading extra python dependencies (ipaddr)
    cidr_regexp = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$"

    previous_subnets = []
    for subnet in module.params['subnets']:
        # check length of description (must be less than 2048 characters)
        if 'description' in subnet:
            if version_info < (3,):
                description_length = len(unicode(subnet['description'], "utf-8"))  # pylint: disable=E0602
            else:
                description_length = len(subnet['description'])

            if description_length > 2048:
                msg = "Description must be less thatn 2048 characters in length."

        # check name
        matches = re.match(name_regexp, subnet['name'])
        if not matches:
            msg = "Subnet name is invalid for subnet '%s'. Subnet name must start with a lowercase letter, " % subnet['name'] \
                + "can contain only lowercase letters, numbers and hyphens, cannot end with a hyphen and cannot be empty."

        # check range
        result = check_subnet_id(subnet['range'])
        if result == 1:
            msg = "subnet range must be a valid cidr range, '%s' is invalid for subnet %s" % (subnet['range'], subnet['name'])
        if result == 2:
            msg = "range of subnet %s must not have a host id part" % subnet['name']

        # check overlapping subnets
        if msg == '':
            for previous_subnet in previous_subnets:
                result = check_overlapping_subnets(subnet['range'], previous_subnet['range'])
                if result:
                    msg = "subnets cannot overlap, but subnet %s and subnet %s do" % (subnet['name'], previous_subnet['name'])
            previous_subnets.append(subnet)

        # check region
        try:
            gce_connection.ex_get_region(subnet['region'])
        except ResourceNotFoundError:
            msg = "subnet region is invalid (%s) for subnet '%s'" % (subnet['region'], subnet['name'])

    if msg:
        module.fail_json(msg=msg, changed=False)


def list_gce_subnets(gce_connection):
    gce_subnets = gce_connection.ex_list_subnetworks()

    results = []
    for gce_subnet in gce_subnets:
        result = dict()
        result['name'] = gce_subnet.name
        result['network'] = gce_subnet.network.name
        result['region'] = gce_subnet.region.name
        result['range'] = gce_subnet.cidr
        result['description'] = gce_subnet.extra['description']
        result['extra'] = dict()
        result['extra']['creation_time'] = gce_subnet.extra['creationTimestamp']
        result['extra']['gateway_address'] = gce_subnet.extra['gatewayAddress']
        result['extra']['self_link'] = gce_subnet.extra['selfLink']
        results.append(result)

    return results


def filter_subnets(subnets, name=None, network=None, region=None, cidr=None):
    if network is not None:
        subnets = [subnet for subnet in subnets if subnet['network'] == network]
    if region is not None:
        subnets = [subnet for subnet in subnets if subnet['region'] == region]
    if cidr is not None:
        subnets = [subnet for subnet in subnets if subnet['cidr'] == cidr]
        subnets = [subnet for subnet in subnets if subnet['region'] == region]
    if name is not None:
        subnets = [subnet for subnet in subnets if subnet['name'] == name]

    return subnets


################################################################################
# Main
################################################################################

def main():
    changed = False

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            mode=dict(default='auto', choices=['legacy', 'auto', 'custom'], type='str'),
            legacy_range=dict(type='str'),
            subnets=dict(type='list'),
            subnet_policy=dict(choices=['ignore_strays', 'include_strays'], type='str'),
            description=dict(type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
        ),
        required_if=[
            ('mode', 'custom', ['subnets', 'subnet_policy']),
            ('mode', 'legacy', ['legacy_range']),
        ],
        mutually_exclusive=[
            ['subnets', 'legacy_range'],
        ],
        supports_check_mode=True,
    )

    check_libs(module)

    # perform further checks on the argument_spec
    additional_constraint_checks(module)

    gce = gce_connect(module, PROVIDER)

    check_parameters(module)

    if module.params['subnets'] is not None:
        check_subnet_parameters(module, gce)

    params = {
        'name': module.params['name'],
        'mode': module.params['mode'],
        'legacy_range': module.params['legacy_range'],
        'subnets': module.params['subnets'],
        'subnet_policy': module.params['subnet_policy'],
        'description': module.params['description'],
        'state': module.params['state'],
    }

    # the created/deleted/updated network object
    network = None

    # this will hold all the subnet that we operated on to use on json_output, nothing else
    passed_subnets = []

    if params['state'] == 'present':

        # check if given network and subnet already exist
        try:
            network = gce.ex_get_network(params['name'])
        except ResourceNotFoundError:
            # user wants to create a new network that doesn't yet exist
            cidr = params['legacy_range'] if params['mode'] == 'legacy' else None
            try:
                network = gce.ex_create_network(params['name'], cidr,
                    mode=params['mode'], description=params['description'],
                    routing_mode='regional')
            except InvalidRequestError as e:
                # probably the supplied cidr was incorrect
                module.fail_json(
                    msg=str(e),
                    changed=False
                )
            else:
                changed = True
        except Exception as e:
            # We are wrapping every gce. method in try-except as there are exceptions
            # that can happen such as timeouts that are not under our contorl.
            module.fail_json(
                msg=str(e),
                changed=False
            )
        else:
            # libcloud currently does not support switching a network from auto
            # to custom mode.
            if network.mode == 'auto' and params['mode'] == 'custom':
                module.fail_json(
                    msg="Currently switching an auto-mode network to custom mode is not supported in Ansible",
                    changed=False
                )

            # Changing between modes any other way than auto->custom is not supported by GCE
            if network.mode != params['mode']:
                module.fail_json(
                    msg="Google Cloud does not allow changing from %s mode to %s" % (network.mode, params['mode']),
                    changed=False
                )

        # SUBNETS
        if params['mode'] == 'custom':
            # below keep in mind that a subnet is uniquelly identified by the tuple (name,region)

            # gce_ variable prefix below denots stuff on the cloud.
            gce_subnets = list_gce_subnets(gce)

            if params['subnet_policy'] == 'include_strays':
                # If there are subnets on GCE that are not mentioned in the argument_spec,
                # we should destroy them before configuring new ones (due to quotas, etc)
                # So, get all subnet on the target network.
                gce_nw_subnets = filter_subnets(gce_subnets, network=params['name'])

                for gce_nw_subnet in gce_nw_subnets:
                    # We filter the user provided subnets to see if the subnet on GCE is actually
                    # included in the argument_spec.
                    found = filter_subnets(params['subnets'], name=gce_nw_subnet['name'], region=gce_nw_subnet['region'])

                    # If the subnet on GCE is not also described in the argument_spec, destroy it.
                    if len(found) == 0:
                        try:
                            gce_nw_subnet = gce.ex_get_subnetwork(gce_nw_subnet['name'], region=gce_nw_subnet['region'])
                            gce.ex_destroy_subnetwork(gce_nw_subnet.name, region=gce_nw_subnet.region)
                        # for some reason libcloud raises InvalidRequestError when is should be raising ResourceInUseError
                        except (ResourceInUseError, InvalidRequestError):
                            module.fail_json(
                                msg="Destroying subnet %s due to include_strays subnet_policy failed because there are instances running" % gce_nw_subnet.name \
                                    + "on that subnet. Other changes may have already occured (check if 'changed': 'true' in the return values).",
                                changed=changed
                            )
                        except Exception as e:
                            if isinstance(gce_nw_subnet, dict):
                                module.fail_json(
                                    msg="When proccessing subnet %s due to include_strays subnet_policy, an error occured occured. " % gce_nw_subnet['name'] \
                                        + "Other changes may have already occured (check if 'changed': 'true' in the return values). Error message: " \
                                        + str(e),
                                    changed=changed
                                )
                            else:
                                module.fail_json(
                                    msg="When proccessing subnet %s due to include_strays subnet_policy, an error occured occured. " % gce_nw_subnet.name \
                                        + "Other changes may have already occured (check if 'changed': 'true' in the return values). Error message: " \
                                        + str(e),
                                    changed=changed
                                )

                        else:
                            changed = True

            # create or update the defined subnets
            for subnet in params['subnets']:
                # See if subnet already exists. gce_subnet will contain 0 or 1 items only due to the tuple.
                gce_subnet = filter_subnets(gce_subnets, name=subnet['name'], region=subnet['region'])

                # it does not exist, so create it
                if len(gce_subnet) == 0:
                    try:
                        gce_subnet = gce.ex_create_subnetwork(subnet['name'], cidr=subnet['range'],
                                                              network=params['name'], region=subnet['region'], description=subnet['description'])
                    except InvalidRequestError as e:
                        # probably the supplied cidr conflicts with an existing subnet
                        module.fail_json(
                            msg="Creating subnet %s failed. Other changes may have already occured (check if " % subnet['name'] \
                                + "'changed': 'true' in the return values). Error message: " + str(e),
                            changed=changed
                        )
                    except Exception as e:
                        module.fail_json(
                            msg="Creating subnet %s failed. Other changes may have already occured (check if " % subnet['name'] \
                                + "'changed': 'true' in the return values). Error message: " + str(e),
                            changed=changed
                        )
                    else:
                        changed = True

                # it exists, but on another network
                elif gce_subnet[0]['network'] != params['name']:
                    module.fail_json(
                        msg="A subnet named '%s' already exists on another network (%s)." % (subnet['name'], gce_subnet[0]['network']),
                        changed=False
                    )
                # it exists on our network, now check if anything has changed
                else:
                    # flatten the list (it becomes a dict)
                    gce_subnet = gce_subnet[0]

                    # GCE does not allow changing subnet description or region.
                    # Changing the region makes no sense and changing the description
                    # is close to useless, so we will not support deleting/inserting,
                    # ie updating the subnet for these options.
                    if gce_subnet['description'] != subnet['description'] or gce_subnet['region'] != subnet['region']:
                        module.fail_json(
                            msg="Google Cloud does not support changing the region or the description of a route.",
                            changed=False
                        )

                    # libcloud currently does not support expanding the subnet.
                    if gce_subnet['range'] != subnet['range']:
                        module.fail_json(
                            msg="Currently, Ansible does not support expanding the subnet range. " \
                                + "Other modifications on the subnet range are not allowed by GCE.",
                            changed=False
                        )

                    # no_update is possible with libcloud 2.0.0.

                passed_subnets.append(gce_subnet)

    if params['state'] == 'absent':

        try:
            network = gce.ex_get_network(params['name'])
        except ResourceNotFoundError:
            pass
        except Exception as e:
            module.fail_json(
                msg=str(e),
                changed=False
            )
        else:
            # If the network mode is different to the one specified, the destruction will fail
            if network.mode != params['mode']:
                module.fail_json(
                    msg="Network %s has a mode of %s on GCE but it is specified in task as mode: %s." \
                        % (params['name'], network.mode, params['mode']),
                    changed=False
                )

            if params['mode'] == 'custom':
                # gce_ variable prefix below denots stuff on the cloud.
                gce_subnets = list_gce_subnets(gce)

                # Get all the subnets in the network that exists on GCE.
                gce_nw_subnets = filter_subnets(gce_subnets, network=params['name'])

                # Destroy only the subnets that are specified in the argument_spec
                if params['subnet_policy'] == 'ignore_strays':
                    for gce_nw_subnet in gce_nw_subnets:
                        # We filter the user provided subnets to see if the subnet on GCE is actually
                        # included in the argument_spec.
                        found = filter_subnets(params['subnets'], name=gce_nw_subnet['name'], region=gce_nw_subnet['region'])

                        # If there is even one subnet on GCE that is missing from the argument_spec, then fail.
                        if len(found) != 0:
                            module.fail_json(
                                msg="subnet_policy=ignore_strays but there are subnets on the network '%s' not specified locally " \
                                    + "and destroying the network will fail. Set subnet_policy=include_strays to destroy all subnets regardless.",
                                changed=False
                            )
                            break

                    # no stray subnet found on GCE, so proceed
                    for subnet in params['subnet']:
                        try:
                            subnet = gce.ex_get_subnetwork(subnet['name'], region=subnet['region'])
                        except ResourceNotFoundError:
                            pass
                        except Exception as e:
                            module.fail_json(
                                msg="Getting subnet %s before destroying failed. Other changes may have already occured (check if " % subnet.name \
                                    + "'changed': 'true' in the return values). Error message: " + str(e),
                                changed=changed
                            )
                        else:
                            try:
                                gce.ex_destroy_subnetwork(subnet)
                            # for some reason libcloud raises InvalidRequestError when is should be raising ResourceInUseError
                            except (ResourceInUseError, InvalidRequestError):
                                module.fail_json(
                                    msg="Destroying subnet %s failed because there are instances running on that subnet. " % subnet.name \
                                        + "Other changes may have already occured (check if 'changed': 'true in the return values).",
                                    changed=changed
                                )
                            except Exception as e:
                                module.fail_json(
                                    msg="Destroying subnet %s failed. Other changes may have already occured (check if " % subnet.name \
                                        + "'changed': 'true' in the return values). Error message: " + str(e),
                                    changed=changed
                                )
                            else:
                                changed = True

                        passed_subnets.append(subnet)

                else:
                    # Note: If we have already destroyed all subnets on previous run, gce_nw_subnets will be empty
                    for gce_nw_subnet in gce_nw_subnets:
                        try:
                            subnet = gce.ex_get_subnetwork(gce_nw_subnet['name'], region=gce_nw_subnet['region'])
                        except ResourceNotFoundError:
                            # We will never be in here due to previous checks, but let's leave it for completeness
                            pass
                        except Exception as e:
                            module.fail_json(
                                msg=str(e),
                                changed=False
                            )
                        else:
                            try:
                                gce.ex_destroy_subnetwork(subnet)
                            # for some reason libcloud raises InvalidRequestError when is should be raising ResourceInUseError
                            except (ResourceInUseError, InvalidRequestError):
                                module.fail_json(
                                    msg="Destroying subnet %s failed because there are instances running on that subnet. " % subnet.name \
                                        + "Other changes may have already occured (check if 'changed': 'true' in the return values).",
                                    changed=changed
                                )
                            except Exception as e:
                                module.fail_json(
                                    msg="Destroying subnet %s failed. Other changes may have already occured (check if " % subnet.name \
                                        + "'changed': 'true' in the return values). Error message: " + str(e),
                                    changed=changed
                                )
                            else:
                                changed = True

            # NETWORK
            try:
                gce.ex_destroy_network(network)
            except Exception as e:
                module.fail_json(
                    msg="Destroying network %s failed. Other changes may have already occured (check if " % network.name \
                        + "'changed': 'true' in the return values). Error message: " + str(e),
                    changed=changed
                )

            changed = True

    json_output = {'changed': changed}
    for value in params:
        if params[value] is not None:
            json_output[value] = params[value]

    # add extra network return values
    extra = dict()
    if network is not None:
        extra['self_Link'] = network.extra['selfLink']
        extra['creation_time'] = network.extra['creationTimestamp']
        if 'gatewayIPv4' in network.extra:
            extra['gateway_ip'] = network.extra['gatewayIPv4']

    json_output.update(extra)

    # add extra subnet return values
    if len(passed_subnets):
        if params['mode'] == 'custom':
            for index, subnet in enumerate(passed_subnets):
                if isinstance(subnet, dict):
                    json_output['subnets'][index].update(subnet['extra'])
                else:
                    json_output['subnets'][index].update(subnet.extra)

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
