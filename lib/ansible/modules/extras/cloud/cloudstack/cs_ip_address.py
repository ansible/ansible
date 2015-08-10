#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Darren Worrall <darren@iweb.co.uk>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_ip_address
short_description: Manages Public/Secondary IP address associations
description:
    - Acquires and associates a public IP to an account. Due to API limitations,
    - this is not an idempotent call, so be sure to only conditionally call this
    - when C(state=present)
version_added: '2.0'
author: "Darren Worrall @dazworrall"
options:
  ip_address:
    description:
      - Public IP address.
      - Required if C(state=absent)
    required: true
  domain:
    description:
      - Domain the IP address is related to.
    required: false
    default: null
  network:
    description:
      - Network the IP address is related to.
    required: false
    default: null
  account:
    description:
      - Account the IP address is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the IP address is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the virtual machine is in.
      - If not set, default zone is used.
    required: false
    default: null
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Associate an IP address
- local_action:
    module: cs_ip_address
    network: My Network
  register: ip_address
  when: create_instance|changed

# Disassociate an IP address
- local_action:
    module: cs_ip_address
    ip_address: 1.2.3.4
    state: absent
'''

RETURN = '''
---
ip_address:
  description: Public IP address.
  returned: success
  type: string
  sample: 1.2.3.4
zone:
  description: Name of zone the IP address is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the IP address is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the IP address is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the IP address is related to.
  returned: success
  type: string
  sample: example domain
'''


try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
class AnsibleCloudStack:

    def __init__(self, module):
        if not has_lib_cs:
            module.fail_json(msg="python library cs required: pip install cs")

        self.result = {
            'changed': False,
        }

        self.module = module
        self._connect()

        self.domain = None
        self.account = None
        self.project = None
        self.ip_address = None
        self.zone = None
        self.vm = None
        self.os_type = None
        self.hypervisor = None
        self.capabilities = None


    def _connect(self):
        api_key = self.module.params.get('api_key')
        api_secret = self.module.params.get('secret_key')
        api_url = self.module.params.get('api_url')
        api_http_method = self.module.params.get('api_http_method')
        api_timeout = self.module.params.get('api_timeout')

        if api_key and api_secret and api_url:
            self.cs = CloudStack(
                endpoint=api_url,
                key=api_key,
                secret=api_secret,
                timeout=api_timeout,
                method=api_http_method
                )
        else:
            self.cs = CloudStack(**read_config())


    def get_or_fallback(self, key=None, fallback_key=None):
        value = self.module.params.get(key)
        if not value:
            value = self.module.params.get(fallback_key)
        return value


    # TODO: for backward compatibility only, remove if not used anymore
    def _has_changed(self, want_dict, current_dict, only_keys=None):
        return self.has_changed(want_dict=want_dict, current_dict=current_dict, only_keys=only_keys)


    def has_changed(self, want_dict, current_dict, only_keys=None):
        for key, value in want_dict.iteritems():

            # Optionally limit by a list of keys
            if only_keys and key not in only_keys:
                continue;

            # Skip None values
            if value is None:
                continue;

            if key in current_dict:

                # API returns string for int in some cases, just to make sure
                if isinstance(value, int):
                    current_dict[key] = int(current_dict[key])
                elif isinstance(value, str):
                    current_dict[key] = str(current_dict[key])

                # Only need to detect a singe change, not every item
                if value != current_dict[key]:
                    return True
        return False


    def _get_by_key(self, key=None, my_dict={}):
        if key:
            if key in my_dict:
                return my_dict[key]
            self.module.fail_json(msg="Something went wrong: %s not found" % key)
        return my_dict


    def get_project(self, key=None):
        if self.project:
            return self._get_by_key(key, self.project)

        project = self.module.params.get('project')
        if not project:
            return None
        args = {}
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        projects = self.cs.listProjects(**args)
        if projects:
            for p in projects['project']:
                if project.lower() in [ p['name'].lower(), p['id'] ]:
                    self.project = p
                    return self._get_by_key(key, self.project)
        self.module.fail_json(msg="project '%s' not found" % project)


    def get_network(self, key=None, network=None):
        if not network:
            network = self.module.params.get('network')

        if not network:
            return None

        args                = {}
        args['account']     = self.get_account('name')
        args['domainid']    = self.get_domain('id')
        args['projectid']   = self.get_project('id')
        args['zoneid']      = self.get_zone('id')

        networks = self.cs.listNetworks(**args)
        if not networks:
            self.module.fail_json(msg="No networks available")

        for n in networks['network']:
            if network in [ n['displaytext'], n['name'], n['id'] ]:
                return self._get_by_key(key, n)
                break
        self.module.fail_json(msg="Network '%s' not found" % network)


    def get_ip_address(self, key=None):
        if self.ip_address:
            return self._get_by_key(key, self.ip_address)

        ip_address = self.module.params.get('ip_address')
        if not ip_address:
            self.module.fail_json(msg="IP address param 'ip_address' is required")

        args = {}
        args['ipaddress'] = ip_address
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        args['projectid'] = self.get_project(key='id')
        args['listall'] = True
        ip_addresses = self.cs.listPublicIpAddresses(**args)

        if ip_addresses:
            self.ip_address = ip_addresses['publicipaddress'][0]
        return self._get_by_key(key, self.ip_address)


    def get_zone(self, key=None):
        if self.zone:
            return self._get_by_key(key, self.zone)

        zone = self.module.params.get('zone')
        zones = self.cs.listZones()

        # use the first zone if no zone param given
        if not zone:
            self.zone = zones['zone'][0]
            return self._get_by_key(key, self.zone)

        if zones:
            for z in zones['zone']:
                if zone in [ z['name'], z['id'] ]:
                    self.zone = z
                    return self._get_by_key(key, self.zone)
        self.module.fail_json(msg="zone '%s' not found" % zone)


    def get_account(self, key=None):
        if self.account:
            return self._get_by_key(key, self.account)

        account = self.module.params.get('account')
        if not account:
            return None

        domain = self.module.params.get('domain')
        if not domain:
            self.module.fail_json(msg="Account must be specified with Domain")

        args = {}
        args['name'] = account
        args['domainid'] = self.get_domain(key='id')
        args['listall'] = True
        accounts = self.cs.listAccounts(**args)
        if accounts:
            self.account = accounts['account'][0]
            return self._get_by_key(key, self.account)
        self.module.fail_json(msg="Account '%s' not found" % account)


    def get_domain(self, key=None):
        if self.domain:
            return self._get_by_key(key, self.domain)

        domain = self.module.params.get('domain')
        if not domain:
            return None

        args = {}
        args['listall'] = True
        domains = self.cs.listDomains(**args)
        if domains:
            for d in domains['domain']:
                if d['path'].lower() in [ domain.lower(), "root/" + domain.lower(), "root" + domain.lower() ] :
                    self.domain = d
                    return self._get_by_key(key, self.domain)
        self.module.fail_json(msg="Domain '%s' not found" % domain)


    # TODO: for backward compatibility only, remove if not used anymore
    def _poll_job(self, job=None, key=None):
        return self.poll_job(job=job, key=key)


    def poll_job(self, job=None, key=None):
        if 'jobid' in job:
            while True:
                res = self.cs.queryAsyncJobResult(jobid=job['jobid'])
                if res['jobstatus'] != 0 and 'jobresult' in res:
                    if 'errortext' in res['jobresult']:
                        self.module.fail_json(msg="Failed: '%s'" % res['jobresult']['errortext'])
                    if key and key in res['jobresult']:
                        job = res['jobresult'][key]
                    break
                time.sleep(2)
        return job


class AnsibleCloudStackIPAddress(AnsibleCloudStack):

    def __init__(self, module):
        AnsibleCloudStack.__init__(self, module)
        self.vm_default_nic = None

    def associate_ip_address(self):
        self.result['changed'] = True
        args = {}
        args['account'] = self.get_account(key='id')
        args['networkid'] = self.get_network(key='id')
        args['zoneid'] = self.get_zone(key='id')
        ip_address = {}
        if not self.module.check_mode:
            res = self.cs.associateIpAddress(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self._poll_job(res, 'ipaddress')
            ip_address = res
        return ip_address

    def disassociate_ip_address(self):
        ip_address = self.get_ip_address()
        if ip_address is None:
            return ip_address
        if ip_address['isstaticnat']:
            self.module.fail_json(msg="IP address is allocated via static nat")

        self.result['changed'] = True
        if not self.module.check_mode:
            res = self.cs.disassociateIpAddress(id=ip_address['id'])
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self._poll_job(res, 'ipaddress')
        return ip_address

    def get_result(self, ip_address):
        if ip_address:
            if 'zonename' in ip_address:
                self.result['zone'] = ip_address['zonename']
            if 'domain' in ip_address:
                self.result['domain'] = ip_address['domain']
            if 'account' in ip_address:
                self.result['account'] = ip_address['account']
            if 'project' in ip_address:
                self.result['project'] = ip_address['project']
            if 'ipaddress' in ip_address:
                self.result['ip_address'] = ip_address['ipaddress']
            if 'id' in ip_address:
                self.result['id'] = ip_address['id']
        return self.result


def main():
    module = AnsibleModule(
        argument_spec = dict(
            ip_address = dict(required=False),
            state = dict(choices=['present', 'absent'], default='present'),
            zone = dict(default=None),
            domain = dict(default=None),
            account = dict(default=None),
            network = dict(default=None),
            project = dict(default=None),
            poll_async = dict(choices=BOOLEANS, default=True),
            api_key = dict(default=None),
            api_secret = dict(default=None, no_log=True),
            api_url = dict(default=None),
            api_http_method = dict(choices=['get', 'post'], default='get'),
            api_timeout = dict(type='int', default=10),
        ),
        required_together = (
            ['api_key', 'api_secret', 'api_url'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_ip_address = AnsibleCloudStackIPAddress(module)

        state = module.params.get('state')
        if state in ['absent']:
            ip_address = acs_ip_address.disassociate_ip_address()
        else:
            ip_address = acs_ip_address.associate_ip_address()

        result = acs_ip_address.get_result(ip_address)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
