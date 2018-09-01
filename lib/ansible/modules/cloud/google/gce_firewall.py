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
module: gce_firewall
version_added: "2.4"
short_description: create/destroy GCE firewall rules
description:
    - This module can create and destroy Google Compute Engine firewall rules
      U(https://cloud.google.com/compute/docs/vpc/firewalls).
      Installation/configuration instructions for the gce_* modules can
      be found at U(https://docs.ansible.com/ansible/guide_gce.html).
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.14.0"
author:
    - "Eric Johnson (@erjohnso) <erjohnso@google.com>"
    - "Tom Melendez (@supertom) <supertom@google.com>"
    - "Nikolaos Kakouros (@tterranigma) <tterranigma@gmail.com>"
options:
    name:
        description:
            - The name of the firewall rule.
        required: true
    network:
        description:
            - The network that the rule will be applied to.
        default: default
    allowed:
        description:
            - The protocol:ports to allow ('tcp:80' or 'tcp:80,443' or 'tcp:80-800;udp:1-25').
            - A value of 'all' allows everything.
        required: true
    src_ranges:
        description:
            - The source IPv4 address range that the rule will filter.
            - It must be an array of subnet addresses in CIDR notation, eg 10.0.0.0/17
            - If both src_ranges and src_tags are empty (or not given), src_ranges defaults to ['0.0.0.0/0']
        aliases: [src_cidr, src_range]
    src_tags:
        description:
            - Traffic originating from these instances will be filtered through the rule.
            - It must be an array of valid instance tags.
            - Tags will be accepted even if there are no instances with those tags assigned.
    target_tags:
        description:
            - The target instances that will be protected by this rule.
            - If not given, the rule will apply to all instances.
    priority:
        description:
            - The priority of the rule
          default: 1000
    state:
        description:
            - Desired state of the firewall.
        default: "present"
        choices: ["present", "absent"]
'''

EXAMPLES = '''
# Create Firewall Rule with Source Tags
- name: Create Firewall Rule w/Source Tags on the default network
  gce_net:
    name: "my-firewall-rule"
    allowed: tcp:80
    src_tags: "foo,bar"

# Allow all traffic for "exposed" instance on a network
- name: Create Firewall Rule w/Source Range
  gce_net:
    name: "my-firewall-rule"
    network: second-net
    allowed: tcp:80
    src_ranges: ['10.1.1.1/32']
    target_tags: exposed
'''

RETURN = '''
name:
  description: Name of the firewall rule.
  returned: always
  type: string
  sample: "my-firewall"

network:
    description: Name of the network.
    returned: always
    type: string
    sample: "my-network"

allowed:
    description: Rules (ports and protocols) specified by this firewall rule.
    returned: always
    type: string
    sample: "tcp:80;icmp"

src_ranges:
    description: IP address blocks a firewall rule applies to.
    returned: when specified
    type: list
    sample: [ '10.1.1.12/8' ]

src_tags:
    description: Instance Tags firewall rule applies to.
    returned: when specified while creating a firewall rule
    type: list
    sample: [ 'foo', 'bar' ]

target_tags:
    description: Instance Tags with these tags receive traffic allowed by firewall rule.
    returned: when specified while creating a firewall rule
    type: list
    sample: [ 'foo', 'bar' ]

priority:
    description: The priority of the rule
    returned: if specified while creating
    type: integer
    sample: 1000
state:
    description: State of the item operated on.
    returned: always
    type: string
    sample: "present"

self_link:
    description: firewall resource uri on GCE
    returned: always, except when I(state=absent) and rule originally does not exist
    type: string
    sample: https://www.googleapis.com/compute/v1/projects/myproject/global/firewalls/myrule

creation_time:
    description: firewall rule creation timestamp
    returned: always, except when I(state=absent) and rule originally does not exist
    type: string
    sample: "2017-06-28T10:59:59.698-07:00"
'''

################################################################################
# Imports
################################################################################

try:
    from libcloud import __version__ as LIBCLOUD_VERSION
    from libcloud.compute.types import Provider
    from libcloud.common.google import ResourceNotFoundError

    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

# module specific imports
from distutils.version import LooseVersion
import re

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect


################################################################################
# Constants
################################################################################

# firewall methods were introduced in 0.14.0
MINIMUM_LIBCLOUD_VERSION = '0.14.0'

try:
    PROVIDER = Provider.GCE
except NameError:
    # libcloud may not have been successfully imported. In that case, execution
    # will stop after check_libs() has been called.
    pass


################################################################################
# Functions
################################################################################

def check_allowed(allowed_string, module):
    # Read the instruction variable!

    msg = ''
    instructions = " NOTE: 'allowed' must be in the form protocol:port. Valid protocols are tcp, "\
        + "udp, icmp, ah, esp, sctp or IP protocol nubmers. The :port part is optional "\
        + "and valid only for tcp and udp. Multiple protocol:port sequences can be combined "\
        + "with semicolons, eg proto1:port1;proto2;proto3:port3-port4. No trailing semicolon is allowed."

    # checks for a trailing semicolon
    semicolon_regexp = r"^(.*)[;]$"

    # checks for numerals from 0 to 255 (IP protocol numbers) or the strngs 'icmp', 'ah', 'esp', 'sctp', 'tcp' or 'udp'
    protocol_regex = r"^([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]|icmp|ah|esp|sctp|tcp|udp)$"

    if allowed_string == 'all':
        return

    if re.match(semicolon_regexp, allowed_string):
        msg = "In option 'allowed', a trailing semicolon is not allowed but one is given."

    for allowed in allowed_string.split(';'):

        # strip whitespace that makes regexes fail
        allowed = allowed.strip()

        # if there are more than two colons, eg tcp:80:2222, it is invalid
        if allowed.count(':') >= 2:
            msg = "In option 'allowed', the '%s' protocol definition is not valid (contains more than one ':')." \
                + instructions

        # if there is no ':' then we expect a protocol, eg icmp or allowed = 8
        elif allowed.count(":") == 0:
            if not re.match(protocol_regex, allowed):
                msg = "In option 'allowed', the '%s' protocol definition is not valid (invalid protocol name/number)." % allowed \
                    + instructions

        # if there is a ':', eg udp:80,22 or tcp:50-2000
        elif allowed.count(":") == 1:
            protocol, ports = allowed.split(":")

            # only tcp and udp are allowed to have ports
            if not re.match(r"^(udp|tcp)$", protocol):
                msg = "In option 'allowed', the '%s' protocol definition is not valid " % allowed \
                    + "(when defining ports the protocol should be either 'tcp' or 'udp', '%s' given)." % protocol \
                    + instructions

            # multiple ports are allowed separated with comma, eg '20,50-200,2222'
            ports = ports.split(',')
            for port in ports:
                if port.count("-") == 0:
                    # make sure the port is a digit ...
                    if not port.isdigit():
                        # port is a string, that's why we are using isdigit
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s')." % (allowed, port) \
                            + instructions
                    # ... that is in the range of valid ports [0-65535]
                    elif not 0 <= int(port) <= 65535:
                        # since port is a string we need to cast it to an integer to make comparisons
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s') outside the [0-65535] range." % (allowed, port) \
                            + instructions

                # a port can be a range, like '50-200'
                if (port.count("-") == 1):
                    port = port.split('-')

                    if not port[1].isdigit():
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s')." % (allowed, port[1]) \
                            + instructions
                    elif not (0 <= int(port[1]) <= 65535):
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s') outside the [0-65535] range." % (allowed, port[1]) \
                            + instructions

                    elif not port[0].isdigit():
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s')." % (allowed, port[0]) \
                            + instructions
                    elif not (0 <= int(port[0]) <= 65535):
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port ('%s') outside the [0-65535] range." % (allowed, port[0]) \
                            + instructions

                    # the range end must be larger that the range start, eg 500-33 or 22-22 are invalid
                    if msg == '' and int(port[0]) >= int(port[1]):
                        # we checked for msg == '' because we only fail at the end of the function. This means
                        # that we might have port[0]=abc which is not a valid numeral, this will be caught by
                        # the previous checks but since we haven't failed yet we will reach here and say int(port[0])
                        # which will fail.
                        msg = "In option 'allowed', the '%s' protocol definition has an invalid port range " % allowed \
                            + "('%s-%s', range end is less than range start)." % (port[0], port[1]) \
                            + instructions
    if msg:
        module.fail_json(msg=msg, changed=False)


def check_parameter_format(module):
    # All the below checks are performed to allow check_mode to give reliable results.
    # Otherwise, we could handle the exceptions raised by libcloud and skip doing
    # duplicate work here.

    msg = ''

    # Starts with lowercase letter, contains only lowercase letters, nubmers, hyphens,
    # cannot be empty, cannot end with hyphen. Taken directly for GCE error responses.
    name_regexp = r"^(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)$"

    # cidr range regexp. Using a regexp to avoid loading extra python
    # dependencies (ipaddr). This will not match everything of course, eg
    # 10.0.0.1/20 will still pass. We will get an exception then, which we
    # handle later in the code. But still, this regex is good enough to save
    # some round trip times.
    cidr_regexp = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$"

    # check the firewall rule name.
    matches = re.match(name_regexp, module.params['name'])
    if matches is None:
        msg = "Firewall name must start with a lowercase letter, can be at most 63 characters, " \
            + "\can contain only lowercase letters, " \
            + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check if given source tags are syntactically valid
    for tag in module.params['src_tags']:
        matches = re.match(name_regexp, tag)

        if matches is None:
            msg = "Source tags must start with a lowercase letter, can contain only lowercase letters, " \
                + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check if target tags are syntactically valid
    if module.params['target_tags'] != 'all':
        for tag in module.params['target_tags']:
            matches = re.match(name_regexp, tag)

            if matches is None:
                msg = "Target tags must start with a lowercase letter, can contain only lowercase letters, " \
                    + "numbers and hyphens, cannot end with a hyphen and cannot be empty."

    # check if the source range is a valid cidr
    for cidr in module.params['src_ranges']:
        matches = re.match(cidr_regexp, cidr)

        if matches is None:
            msg = "src_ranges must be a list of valid cidr ranges, range '%s' is invalid" % cidr

    if msg:
        module.fail_json(msg=msg, changed=False)

    if module.params['allowed'] is not None:
        check_allowed(module.params['allowed'], module)


def check_network_exists(gce_connection, module):
    # if state=absent we do not care if the network exists,
    # just delete whatever is there.
    if module.params['state'] == 'present':
        try:
            gce_connection.ex_get_network(module.params['network'])
        except ResourceNotFoundError:
            module.fail_json(
                msg="No network '%s' found." % module.params['network'],
                changed=False
            )


def format_allowed_section(allowed):
    """Format each section of the allowed list"""
    if allowed.count(":") == 0:
        protocol = allowed
        ports = []
    else:  # count(":") == 1
        protocol, ports = allowed.split(":")

    if ports.count(","):
        ports = ports.split(",")
    elif ports:
        ports = [ports]
    return_val = {"IPProtocol": protocol}
    if ports:
        return_val["ports"] = ports
    return return_val


def format_allowed(allowed):
    """Format the 'allowed' value so that it is GCE compatible."""
    return_value = []
    if allowed.count(";") == 0:
        return [format_allowed_section(allowed)]
    else:
        sections = allowed.split(";")
        for section in sections:
            return_value.append(format_allowed_section(section))
    return return_value


def port_sorter(protos):
    for index, proto in enumerate(protos):
        ports = proto.get('ports', [])
        protos[index]['ports'] = sorted(ports)
    return protos


def sorted_allowed_list(allowed_list):
    """Sort allowed_list (output of format_allowed) by protocol and port."""
    # sort by protocol
    allowed_by_protocol = sorted(allowed_list, key=lambda x: x['IPProtocol'])

    # sort the ports list
    all_sorted = port_sorter(allowed_by_protocol)

    return all_sorted


def check_libcloud(module):
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


def set_empty_defaults(module):
    # If both src_tags and src_ranges are None (unset), libcloud will set src_ranges
    # to ['0.0.0.0/0']. Of course, we set both src_tags and src_ranges to []. So,
    # that will no happen. As a result, the firewall creation will fail when the
    # request reaches GCE. Here we check if both are [] and set src_ranges to
    # ['0.0.0.0/0'] like libcloud. We cannot unset the defaults of [] and let the
    # variables be None because we may need to loop them later in the code, which
    # would cause errors if they were None.
    if module.params['src_tags'] == [] and module.params['src_ranges'] == []:
        module.params['src_ranges'] = ['0.0.0.0/0']


################################################################################
# Main
################################################################################

def main():
    changed = False

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type="str"),
            network=dict(default='default', type="str"),
            allowed=dict(type="str"),
            src_ranges=dict(type='list', default=[], aliases=['src_cidr', 'src_range']),
            src_tags=dict(type='list', default=[]),
            target_tags=dict(type='list', default=[]),
            state=dict(default='present', choices=['present', 'absent'], type="str"),
            priority=dict(default=1000, type="int")
        ),
        required_if=[
            ('state', 'present', ['allowed'])
        ],
        supports_check_mode=True,
    )

    check_libcloud(module)

    set_empty_defaults(module)

    check_parameter_format(module)

    params = {
        'name': module.params['name'],
        'network': module.params['network'],
        'allowed': module.params['allowed'],
        'src_ranges': module.params['src_ranges'],
        'src_tags': module.params['src_tags'],
        'target_tags': module.params['target_tags'],
        'priority': module.params['priority'],
        'state': module.params['state'],
    }

    gce = gce_connect(module, PROVIDER)

    check_network_exists(gce, module)

    fw = None

    if params['state'] == 'present':
        allowed_list = format_allowed(params['allowed'])

        # Fetch existing rule and if it exists, compare attributes
        # update if attributes changed. Create if doesn't exist.
        try:
            fw = gce.ex_get_firewall(params['name'])
        except ResourceNotFoundError:
            # Firewall rule not found so we try to create it.
            if not module.check_mode:
                try:
                    fw = gce.ex_create_firewall(params['name'], allowed_list, network=params['network'],
                                                source_ranges=params['src_ranges'], source_tags=params['src_tags'],
                                                target_tags=params['target_tags'], priority=params['priority'])
                except Exception as e:
                    # We are wrapping every gce. method in try-except as there are exceptions
                    # that can happen such as timeouts that are not under our control.
                    module.fail_json(
                        msg=str(e),
                        changed=False
                    )
            changed = True
        except Exception as e:
            module.fail_json(
                msg=str(e),
                changed=False
            )
        else:
            # If old and new attributes are different, we update the firewall rule.
            # This implicitly lets us clear out attributes as well.

            # GCE does not support changing the network of a rule. If changed in
            # the playbook, we will trigger an error to be explicit to the user.
            # We could delete the rule and create a new one, thus "updating",
            # but the use case is extremely limited
            if fw.extra['network_name'] != params['network']:
                module.fail_json(
                    msg="Changing the network of a rule is not supported.",
                    changed=False
                )

            # allowed_list
            if sorted_allowed_list(allowed_list) != sorted_allowed_list(fw.allowed):
                fw.allowed = allowed_list
                changed = True

            # source_tags might be None; cast it to an empty list
            if fw.source_ranges is None:
                fw.source_ranges = []

            if fw.source_ranges != params['src_ranges']:
                # If these attributes are lists, we sort them first, then compare.
                # Otherwise, we update if they differ.
                if isinstance(params['src_ranges'], list):
                    if sorted(fw.source_ranges) != sorted(params['src_ranges']):
                        fw.source_ranges = params['src_ranges']
                        changed = True
                else:
                    fw.source_ranges = params['src_ranges']
                    changed = True

            # source_tags might be None; cast it to an empty list
            if fw.source_tags is None:
                fw.source_tags = []

            if fw.source_tags != params['src_tags']:
                if isinstance(params['src_tags'], list):
                    if sorted(fw.source_tags) != sorted(params['src_tags']):
                        fw.source_tags = params['src_tags']
                        changed = True

                else:
                    fw.source_tags = params['src_tags']
                    changed = True

            # target_tags might be None; cast it to an empty list
            if fw.target_tags is None:
                fw.target_tags = []

            if fw.target_tags != params['target_tags']:
                if isinstance(params['target_tags'], list):
                    if sorted(fw.target_tags) != sorted(params['target_tags']):
                        fw.target_tags = params['target_tags']
                        changed = True

                else:
                    fw.target_tags = params['target_tags']
                    changed = True

            if fw.priority != params['priority']:
                module.warn("Priority cannot be changed on existing rule")

            if changed is True:
                if not module.check_mode:
                    try:
                        fw = gce.ex_update_firewall(fw)
                    except Exception as e:
                        module.fail_json(
                            msg=str(e),
                            changed=False
                        )
                # unneeded but given for consinstency
                changed = True

    if params['state'] == 'absent':
        try:
            fw = gce.ex_get_firewall(params['name'])
        except ResourceNotFoundError:
            pass
        except Exception as e:
            module.fail_json(
                msg=str(e),
                changed=False
            )
        else:
            if not module.check_mode:
                try:
                    gce.ex_destroy_firewall(fw)
                except Exception as e:
                    module.fail_json(
                        msg=str(e),
                        changed=False
                    )
            params['network'] = fw.extra['network_name']
            params['src_ranges'] = fw.source_ranges
            params['src_tags'] = fw.source_tags
            params['target_tags'] = fw.target_tags
            params['description'] = fw.extra['description']
            changed = True

    json_output = {'changed': changed}
    for value in params:
        if params[value] is not None:
            json_output[value] = params[value]

    # add extra return values
    extra = dict()
    if fw is not None:
        extra['self_Link'] = fw.extra['selfLink']
        extra['creation_time'] = fw.extra['creationTimestamp']
    json_output.update(extra)

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
