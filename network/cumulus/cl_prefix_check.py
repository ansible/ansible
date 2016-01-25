#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
#
# This file is part of Ansible
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cl_prefix_check
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Check to see if route/prefix exists
description:
    - Check to see if a route exists. This module can be used simply to check a
      route and return if its present or absent. A larger timeout can be
      provided to check if a route disappears. An example would be the user
      could change the OSPF cost of a node within the network then utilize
      cl_prefix_check of another (separate) node to verify the node (where the
      OSPF cost was changed) is not being use to route traffic.
options:
    prefix:
        description:
            - route/prefix that module is checking for. Uses format acceptable
              to "ip route show" command. See manpage of "ip-route" for more
              details
        required: true
    state:
        description:
            - Describes if the prefix should be present.
        choices: ['present', 'absent']
        default: ['present']
    timeout:
        description:
            - timeout in seconds to wait for route condition to be met
        default: 5
    poll_interval:
        description:
            - poll interval in seconds to check route.
        default: 1
    nonexthop:
        description:
            - address of node is not desired in result to prefix
        default: ""
    nexthop:
        description:
            - address of node is desired in result to prefix
        default: ""

notes:
    - IP Route Documentation -
      http://manpages.ubuntu.com/manpages/precise/man8/route.8.html
'''
EXAMPLES = '''
Example playbook entries using the cl_prefix_check module to check if a prefix
exists

    tasks:
    - name:  Test if prefix is present.
      cl_prefix_check: prefix=4.4.4.0/24

    - name: Test if route is absent. poll for 200 seconds. Poll interval at
      default setting of 1 second
      cl_prefix_check: prefix=10.0.1.0/24 timeout=200 state=absent

    - name: Test if route is present, with a timeout of 10 seconds and poll
      interval of 2 seconds
      cl_prefix_check: prefix=10.1.1.0/24 timeout=10 poll_interval=2

    - name: Test if route is present, with a nexthop of 4.4.4.4 will fail if no
      nexthop of 5.5.5.5
      cl_prefix_check: prefix=4.4.4.4 nexthop=5.5.5.5

    - name: Test if route is present, with no nexthop of 3.3.3.3 will fail if
      there is a nexthop of 6.6.6.6
      cl_prefix_check: prefix=3.3.3.3 nonexthop=6.6.6.6


'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

def run_cl_cmd(module, cmd, check_rc=True):
    try:
        (rc, out, err) = module.run_command(cmd, check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)
    # trim last line as it is always empty
    ret = out.splitlines()
    f = open('workfile', 'w')
    for a in ret:
        f.write(a)
    return ret

def route_is_present(result):
    if len(result) > 0:
        return True

def route_is_absent(result):
    if len(result) == 0:
        return True

def check_hop(result,hop):
    for line in result:
        if hop in line.split():
            return True
    return False

def check_next_hops(module, result):
    nexthop = module.params.get('nexthop')
    nonexthop = module.params.get('nonexthop')
    prefix = module.params.get('prefix')

    if not nexthop and not nonexthop:
        return True
    elif not nexthop and nonexthop:
        if check_hop(result,nonexthop)==False:
            return True
    elif nexthop and not nonexthop:
        if check_hop(result,nexthop)==True:
            return True
    elif nexthop and nonexthop:
        if check_hop(result,nexthop)==True and check_hop(result,nonexthop)==False:
            return True
    else:
        return false

def loop_route_check(module):
    prefix = module.params.get('prefix')
    state = module.params.get('state')
    timeout = int(module.params.get('timeout'))
    poll_interval = int(module.params.get('poll_interval'))

    # using ip route show instead of ip route get
    # because ip route show will be blank if the exact prefix
    # is missing from the table. ip route get tries longest prefix
    # match so may match default route.
    # command returns empty array if prefix is missing
    cl_prefix_cmd = '/sbin/ip route show %s' % (prefix)
    time_elapsed = 0
    while True:
        result = run_cl_cmd(module, cl_prefix_cmd)
        if state == 'present' and route_is_present(result):
            if check_next_hops(module, result)==True:
                return True
        if state == 'absent' and route_is_absent(result):
            if check_next_hops(module, result)==True:
                return True
        time.sleep(poll_interval)
        time_elapsed += poll_interval
        if time_elapsed == timeout:
            return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            prefix=dict(required=True, type='str'),
            state=dict(default='present', type='str',
                       choices=['present', 'absent']),
            timeout=dict(default=2, type='int'),
            poll_interval=dict(default=1, type='int'),
            nexthop=dict(default='', type='str'),
            nonexthop=dict(default='', type='str'),

        ),
    )

    _state = module.params.get('state')
    _timeout = module.params.get('timeout')
    _msg = "Testing whether route is %s. " % (_state)
    _nexthop = module.params.get('nexthop')
    _nonexthop = module.params.get('nonexthop')

    #checking for bad parameters
    if _nexthop == _nonexthop and _nexthop != '':
        module.fail_json(msg='nexthop and nonexthop cannot be the same')

    #the loop
    if loop_route_check(module):
	        _msg += 'Condition Met'
	        module.exit_json(msg=_msg, changed=False)
    else:
	        _msg += 'Condition not met %s second timer expired' % (_timeout)
	        module.fail_json(msg='paremeters not found')

# import module snippets
from ansible.module_utils.basic import *
import time
# from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
