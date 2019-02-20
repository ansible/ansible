#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_configuration
short_description: Manages configuration on Apache CloudStack based clouds.
description:
    - Manages global, zone, account, storage and cluster configurations.
version_added: '2.1'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the configuration.
    type: str
    required: true
  value:
    description:
      - Value of the configuration.
    type: str
    required: true
  account:
    description:
      - Ensure the value for corresponding account.
    type: str
  domain:
    description:
      - Domain the account is related to.
      - Only considered if I(account) is used.
    type: str
    default: ROOT
  zone:
    description:
      - Ensure the value for corresponding zone.
    type: str
  storage:
    description:
      - Ensure the value for corresponding storage pool.
    type: str
  cluster:
    description:
      - Ensure the value for corresponding cluster.
    type: str
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure global configuration
  cs_configuration:
    name: router.reboot.when.outofband.migrated
    value: false
  delegate_to: localhost

- name: Ensure zone configuration
  cs_configuration:
    name: router.reboot.when.outofband.migrated
    zone: ch-gva-01
    value: true
  delegate_to: localhost

- name: Ensure storage configuration
  cs_configuration:
    name: storage.overprovisioning.factor
    storage: storage01
    value: 2.0
  delegate_to: localhost

- name: Ensure account configuration
  cs_configuration:
    name: allow.public.user.templates
    value: false
    account: acme inc
    domain: customers
  delegate_to: localhost
'''

RETURN = '''
---
category:
  description: Category of the configuration.
  returned: success
  type: str
  sample: Advanced
scope:
  description: Scope (zone/cluster/storagepool/account) of the parameter that needs to be updated.
  returned: success
  type: str
  sample: storagepool
description:
  description: Description of the configuration.
  returned: success
  type: str
  sample: Setup the host to do multipath
name:
  description: Name of the configuration.
  returned: success
  type: str
  sample: zone.vlan.capacity.notificationthreshold
value:
  description: Value of the configuration.
  returned: success
  type: str
  sample: "0.75"
account:
  description: Account of the configuration.
  returned: success
  type: str
  sample: admin
Domain:
  description: Domain of account of the configuration.
  returned: success
  type: str
  sample: ROOT
zone:
  description: Zone of the configuration.
  returned: success
  type: str
  sample: ch-gva-01
cluster:
  description: Cluster of the configuration.
  returned: success
  type: str
  sample: cluster01
storage:
  description: Storage of the configuration.
  returned: success
  type: str
  sample: storage01
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackConfiguration(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackConfiguration, self).__init__(module)
        self.returns = {
            'category': 'category',
            'scope': 'scope',
            'value': 'value',
        }
        self.storage = None
        self.account = None
        self.cluster = None

    def _get_common_configuration_args(self):
        args = {
            'name': self.module.params.get('name'),
            'accountid': self.get_account(key='id'),
            'storageid': self.get_storage(key='id'),
            'zoneid': self.get_zone(key='id'),
            'clusterid': self.get_cluster(key='id'),
        }
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
            args = {
                'name': cluster_name,
            }
            clusters = self.query_api('listClusters', **args)
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
            args = {
                'name': storage_pool_name,
            }
            storage_pools = self.query_api('listStoragePools', **args)
            if storage_pools:
                self.storage = storage_pools['storagepool'][0]
                self.result['storage'] = self.storage['name']
            else:
                self.module.fail_json(msg="Storage pool %s not found." % storage_pool_name)
        return self._get_by_key(key=key, my_dict=self.storage)

    def get_configuration(self):
        configuration = None
        args = self._get_common_configuration_args()
        args['fetch_list'] = True
        configurations = self.query_api('listConfigurations', **args)
        if not configurations:
            self.module.fail_json(msg="Configuration %s not found." % args['name'])
        for config in configurations:
            if args['name'] == config['name']:
                configuration = config
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
                res = self.query_api('updateConfiguration', **args)
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
        name=dict(required=True),
        value=dict(type='str', required=True),
        zone=dict(),
        storage=dict(),
        cluster=dict(),
        account=dict(),
        domain=dict(default='ROOT')
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_configuration = AnsibleCloudStackConfiguration(module)
    configuration = acs_configuration.present_configuration()
    result = acs_configuration.get_result(configuration)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
