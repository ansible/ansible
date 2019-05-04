#!/usr/bin/python

# Copyright: (c) 2019, Chris Redit, github.com/chrisred
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: virt_pool_facts
short_description: Retrieve facts about a libvirt storage pool.
description: Retrieve facts about a libvirt storage pool. Facts from the file config and live config
  are both retrieved when applicable.
version_added: "2.9"
author: Chris Redit (@chrisred)
options:
  name:
    description: Defines the name of the storage pool(s) to retrieve facts for. If no I(name) parameter
      is provided all storage pools on the host will be retrieved.
    type: list
  uri:
    description: The libvirt connection URI.
    default: qemu:///system
    type: str
notes:
  - Facts are generated from the XML configuration of the storage pool. The keys returned for each of
    the items listed in the return values can vary based on the pool configuration.
requirements:
  - python >= 2.6
  - python-lxml
  - libvirt-python
'''

EXAMPLES = '''
- name: Retrieve facts for all the pools on a host
  virt_net_facts:

- name: Retrieve facts for the pools mypool1 and mypool2
  virt_net_facts: name=mypool1,mypool2

- name: Retrieve the free space for all storage pools configured on the host
  virt_pool_facts:
- debug:
    msg: "{{item.key}}: {{item.value.available | filesizeformat(True)}}"
  loop: "{{virt_pools_live | dict2items}}"
  loop_control:
    label: "{{item.key}}"
'''

RETURN = '''
virt_pools:
  description: Facts retrieved from the persistent storage pool config, with the storage pool
    name as a key.
  returned: always
  type: complex
  contains:
    active:
      description: Defines whether the pool is active or stopped.
      returned: success
      type: bool
    autostart:
      description: Defines whether the pool will start automatically after the host has booted.
      returned: success
      type: bool
    allocation:
      description: The total storage allocation for the pool (bytes).
      returned: success
      type: str
    available:
      description: The free space available for allocating new volumes in the pool (bytes).
      returned: success
      type: str
    capacity:
      description: The total storage capacity for the pool (bytes).
      returned: success
      type: str
    name:
      description: The short name for the pool.
      returned: success
      type: str
    persistent:
      description: Defines whether the pool is persistent or transient.
      returned: success
      type: bool
    type:
      description: The pool type.
      returned: success
      type: str
    uuid:
      description: The globally unique identifier for the pool.
      returned: success
      type: str
    refresh:
      description: Defines how the pool and associated volumes are refreshed.
      returned: success
      type: complex
    source:
      description: The source of the pool.
      returned: success
      type: complex
    target:
      description: The mapping of the pool to the host file system.
      returned: success
      type: complex
virt_pools_live:
  description: Facts retrieved from the live storage pool config, with the storage pool name
    as a key. This contains an identical set of return values as the C(virt_pools) key.
  returned: always
  type: complex
  contains: dict
'''

from ansible.module_utils.basic import (AnsibleModule, missing_required_lib)
from ansible.module_utils.virt import (Config, etree_to_dict, flatten_dict, get_facts)
import traceback

LIBVIRT_IMPORT_ERROR = None
try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    LIBVIRT_IMPORT_ERROR = traceback.format_exc()
    HAS_LIBVIRT = False


class PoolConfig(Config):
    @property
    def allocation(self):
        return self._etree.findtext('./allocation')

    @property
    def available(self):
        return self._etree.findtext('./available')

    @property
    def capacity(self):
        return self._etree.findtext('./capacity')

    @property
    def name(self):
        return self._etree.findtext('./name')

    @property
    def type(self):
        return self._etree.find('.').attrib.get('type')

    @property
    def uuid(self):
        return self._etree.findtext('./uuid')

    @property
    def refresh(self):
        return self._etree.find("./refresh")

    @property
    def source(self):
        return self._etree.find("./source")

    @property
    def target(self):
        return self._etree.find("./target")


def main():
    module_args = dict(
        name=dict(type='list'),
        uri=dict(type='str', default='qemu:///system'),
    )

    host = None
    config_live = None
    config_file = None
    active = False
    autostart = None
    persistent = True
    facts_file = dict()
    facts_live = dict()
    pools = list()
    module = AnsibleModule(module_args, supports_check_mode=True)
    name = module.params['name']

    if not HAS_LIBVIRT:
        module.fail_json(msg=missing_required_lib('libvirt'), exception=LIBVIRT_IMPORT_ERROR)

    try:
        host = libvirt.open(module.params['uri'])
        try:
            if name is not None and isinstance(name, list):
                pools = [host.storagePoolLookupByName(item) for item in name]
            else:
                pools = host.listAllStoragePools(
                    libvirt.VIR_CONNECT_LIST_STORAGE_POOLS_PERSISTENT |
                    libvirt.VIR_CONNECT_LIST_STORAGE_POOLS_TRANSIENT
                )
        except libvirt.libvirtError:
            module.fail_json(msg='Storage Pool(s) not found on this host.')

        # the properties of the Config object that will be returned as facts
        wanted_properties = [
            'allocation', 'available', 'capacity', 'name', 'type', 'uuid', 'refresh', 'source',
            'target'
        ]

        for pool in pools:
            if pool.isPersistent():
                config_file = PoolConfig(module, pool.XMLDesc(libvirt.VIR_STORAGE_XML_INACTIVE))
                autostart = True if pool.autostart() else False

                if pool.isActive():
                    config_live = PoolConfig(module, pool.XMLDesc())
                    active = True
            else:
                # a transient pool only has a "live" configuration
                config_live = PoolConfig(module, pool.XMLDesc())
                active = True
                persistent = False

            if config_file:
                facts_file[config_file.name] = get_facts(config_file, wanted_properties)
                facts_file[config_file.name]['active'] = active
                facts_file[config_file.name]['autostart'] = autostart
                facts_file[config_file.name]['persistent'] = persistent

            if config_live:
                facts_live[config_live.name] = get_facts(config_live, wanted_properties)
                facts_live[config_live.name]['active'] = active
                facts_live[config_live.name]['autostart'] = autostart
                facts_live[config_live.name]['persistent'] = persistent

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                virt_pools=facts_file if len(facts_file) > 0 else None,
                virt_pools_live=facts_live if len(facts_live) > 0 else None,
            ),
        )

    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        if host is not None:
            host.close()


if __name__ == '__main__':
    main()
