#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
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
module: cs_configuration
short_description: Manages configuration on Apache CloudStack based clouds.
description:
    - Manages global, zone, account, storage and cluster configurations.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the configuration.
    required: true
  value:
    description:
      - Value of the configuration.
    required: true
  account:
    description:
      - Ensure the value for corresponding account.
    required: false
    default: null
  domain:
    description:
      - Domain the account is related to.
      - Only considered if C(account) is used.
    required: false
    default: ROOT
  zone:
    description:
      - Ensure the value for corresponding zone.
    required: false
    default: null
  storage:
    description:
      - Ensure the value for corresponding storage pool.
    required: false
    default: null
  cluster:
    description:
      - Ensure the value for corresponding cluster.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure global configuration
- local_action:
    module: cs_configuration
    name: router.reboot.when.outofband.migrated
    value: false

# Ensure zone configuration
- local_action:
    module: cs_configuration
    name: router.reboot.when.outofband.migrated
    zone: ch-gva-01
    value: true

# Ensure storage configuration
- local_action:
    module: cs_configuration
    name: storage.overprovisioning.factor
    storage: storage01
    value: 2.0

# Ensure account configuration
- local_action:
    module: cs_configuration:
    name: allow.public.user.templates
    value: false
    account: acme inc
    domain: customers
'''

RETURN = '''
---
category:
  description: Category of the configuration.
  returned: success
  type: string
  sample: Advanced
scope:
  description: Scope (zone/cluster/storagepool/account) of the parameter that needs to be updated.
  returned: success
  type: string
  sample: storagepool
description:
  description: Description of the configuration.
  returned: success
  type: string
  sample: Setup the host to do multipath
name:
  description: Name of the configuration.
  returned: success
  type: string
  sample: zone.vlan.capacity.notificationthreshold
value:
  description: Value of the configuration.
  returned: success
  type: string
  sample: "0.75"
account:
  description: Account of the configuration.
  returned: success
  type: string
  sample: admin
Domain:
  description: Domain of account of the configuration.
  returned: success
  type: string
  sample: ROOT
zone:
  description: Zone of the configuration.
  returned: success
  type: string
  sample: ch-gva-01
cluster:
  description: Cluster of the configuration.
  returned: success
  type: string
  sample: cluster01
storage:
  description: Storage of the configuration.
  returned: success
  type: string
  sample: storage01
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackConfiguration(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackConfiguration, self).__init__(module)
        self.returns = {
            'category': 'category',
            'scope':    'scope',
            'value':    'value',
        }
        self.storage = None
        self.account = None
        self.cluster = None


    def _get_common_configuration_args(self):
        args = {}
        args['name'] = self.module.params.get('name')
        args['accountid'] = self.get_account(key='id')
        args['storageid'] = self.get_storage(key='id')
        args['zoneid'] = self.get_zone(key='id')
        args['clusterid'] = self.get_cluster(key='id')
        return args


    def get_zone(self, key=None):
        # make sure we do net use the default zone
        zone = self.module.params.get('zone')
        if zone:
            return super(AnsibleCloudStackConfiguration, self).get_zone(key=key)


    def get_cluster(self, key=None):
        if not self.cluster:
            cluster_name = self.module.params.get('cluster')
            if not cluster_name:
                return None
            args = {}
            args['name'] = cluster_name
            clusters = self.cs.listClusters(**args)
            if clusters:
                self.cluster = clusters['cluster'][0]
                self.result['cluster'] = self.cluster['name']
            else:
                self.module.fail_json(msg="Cluster %s not found." % cluster_name)
        return self._get_by_key(key=key, my_dict=self.cluster)


    def get_storage(self, key=None):
        if not self.storage:
            storage_pool_name = self.module.params.get('storage')
            if not storage_pool_name:
                return None
            args = {}
            args['name'] = storage_pool_name
            storage_pools = self.cs.listStoragePools(**args)
            if storage_pools:
                self.storage = storage_pools['storagepool'][0]
                self.result['storage'] = self.storage['name']
            else:
                self.module.fail_json(msg="Storage pool %s not found." % storage_pool_name)
        return self._get_by_key(key=key, my_dict=self.storage)


    def get_configuration(self):
        configuration = None
        args = self._get_common_configuration_args()
        configurations = self.cs.listConfigurations(**args)
        if not configurations:
            self.module.fail_json(msg="Configuration %s not found." % args['name'])
        configuration = configurations['configuration'][0]
        return configuration


    def get_value(self):
        value = str(self.module.params.get('value'))
        if value in ('True', 'False'):
            value = value.lower()
        return value


    def present_configuration(self):
        configuration = self.get_configuration()
        args = self._get_common_configuration_args()
        args['value'] = self.get_value()
        if self.has_changed(args, configuration, ['value']):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.updateConfiguration(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                configuration = res['configuration']
        return configuration


    def get_result(self, configuration):
        self.result = super(AnsibleCloudStackConfiguration, self).get_result(configuration)
        if self.account:
            self.result['account'] = self.account['name']
            self.result['domain'] = self.domain['path']
        elif self.zone:
            self.result['zone'] = self.zone['name']
        return self.result

def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
        value = dict(type='str', required=True),
        zone = dict(default=None),
        storage = dict(default=None),
        cluster = dict(default=None),
        account = dict(default=None),
        domain = dict(default='ROOT')
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_configuration = AnsibleCloudStackConfiguration(module)
        configuration = acs_configuration.present_configuration()
        result = acs_configuration.get_result(configuration)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
