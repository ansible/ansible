#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Michael Perzel
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

DOCUMENTATION = '''
---
module: bigip_gtm_wide_ip
short_description: "Manages F5 BIG-IP GTM wide ip"
description:
    - "Manages F5 BIG-IP GTM wide ip"
version_added: "2.0"
author:
    - Michael Perzel (@perzizzle)
    - Tim Rupp (@caphrim007)
notes:
    - "Requires BIG-IP software version >= 11.4"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Tested with manager and above account privilege level"

requirements:
    - bigsuds
options:
    lb_method:
        description:
            - LB method of wide ip
        required: true
        choices: ['return_to_dns', 'null', 'round_robin',
                      'ratio', 'topology', 'static_persist', 'global_availability',
                      'vs_capacity', 'least_conn', 'lowest_rtt', 'lowest_hops',
                      'packet_rate', 'cpu', 'hit_ratio', 'qos', 'bps',
                      'drop_packet', 'explicit_ip', 'connection_rate', 'vs_score']
    wide_ip:
        description:
            - Wide IP name
        required: true
extends_documentation_fragment: f5
'''

EXAMPLES = '''
  - name: Set lb method
    local_action: >
      bigip_gtm_wide_ip
      server=192.0.2.1
      user=admin
      password=mysecret
      lb_method=round_robin
      wide_ip=my-wide-ip.example.com
'''

try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.f5 import bigip_api, f5_argument_spec


def get_wide_ip_lb_method(api, wide_ip):
    lb_method = api.GlobalLB.WideIP.get_lb_method(wide_ips=[wide_ip])[0]
    lb_method = lb_method.strip().replace('LB_METHOD_', '').lower()
    return lb_method

def get_wide_ip_pools(api, wide_ip):
    try:
        return api.GlobalLB.WideIP.get_wideip_pool([wide_ip])
    except Exception:
        e = get_exception()
        print(e)

def wide_ip_exists(api, wide_ip):
    # hack to determine if wide_ip exists
    result = False
    try:
        api.GlobalLB.WideIP.get_object_status(wide_ips=[wide_ip])
        result = True
    except bigsuds.OperationFailed:
        e = get_exception()
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def set_wide_ip_lb_method(api, wide_ip, lb_method):
    lb_method = "LB_METHOD_%s" % lb_method.strip().upper()
    api.GlobalLB.WideIP.set_lb_method(wide_ips=[wide_ip], lb_methods=[lb_method])

def main():
    argument_spec = f5_argument_spec()

    lb_method_choices = ['return_to_dns', 'null', 'round_robin',
                                    'ratio', 'topology', 'static_persist', 'global_availability',
                                    'vs_capacity', 'least_conn', 'lowest_rtt', 'lowest_hops',
                                    'packet_rate', 'cpu', 'hit_ratio', 'qos', 'bps',
                                    'drop_packet', 'explicit_ip', 'connection_rate', 'vs_score']
    meta_args = dict(
        lb_method = dict(type='str', required=True, choices=lb_method_choices),
        wide_ip = dict(type='str', required=True)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    server_port = module.params['server_port']
    user = module.params['user']
    password = module.params['password']
    wide_ip = module.params['wide_ip']
    lb_method = module.params['lb_method']
    validate_certs = module.params['validate_certs']

    result = {'changed': False}  # default

    try:
        api = bigip_api(server, user, password, validate_certs, port=server_port)

        if not wide_ip_exists(api, wide_ip):
            module.fail_json(msg="wide ip %s does not exist" % wide_ip)

        if lb_method is not None and lb_method != get_wide_ip_lb_method(api, wide_ip):
            if not module.check_mode:
                set_wide_ip_lb_method(api, wide_ip, lb_method)
                result = {'changed': True}
            else:
                result = {'changed': True}

    except Exception:
        e = get_exception()
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
