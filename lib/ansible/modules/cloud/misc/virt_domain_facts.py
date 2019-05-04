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
module: virt_domain_facts
short_description: Retrieve facts about a libvirt domain.
description: Retrieve facts about a libvirt domain. Facts from the file config and live config
  are both retrieved when applicable.
version_added: "2.9"
author: Chris Redit (@chrisred)
options:
  name:
    description: Defines the name of the domain(s) to retrieve facts for. If no I(name) parameter
      is provided all domains on the host will be retrieved.
    type: list
  uri:
    description: The libvirt connection URI.
    default: qemu:///system
    type: str
notes:
  - Facts are generated from the XML configuration of the domain. The keys returned for each of
    the items listed in the return values can vary based on the domain configuration.
requirements:
  - python >= 2.6
  - python-lxml
  - libvirt-python
'''

EXAMPLES = '''
- name: Retrieve facts for all the domains on a host
  virt_domain_facts:

- name: Retrieve facts for the domains mydomain1 and mydomain2
  virt_domain_facts: name=mydomain1,mydomain2

- name: Retrieve every MAC address for each domain on a host
  virt_domain_facts:
- debug:
    msg: "{{item.key}}: {{item.value.interface | map(attribute='mac_address') | join(', ')}}"
  loop: "{{virt_domains | dict2items}}"
  loop_control:
    label: "{{item.key}}"
'''

RETURN = '''
virt_domains:
  description: Facts retrieved from the persistent domain config, with the domain name as a key.
  returned: always
  type: complex
  contains:
    active:
      description: Defines whether the domain is active or stopped.
      returned: success
      type: bool
    autostart:
      description: Defines whether the domain will start automatically after the host has booted.
      returned: success
      type: bool
    emulator:
      description: The path to the device model emulator binary for the domain.
      returned: success
      type: str
    id:
      description: The identifier for a running domain.
      returned: success
      type: str
    name:
      description: The short name for the domain.
      returned: success
      type: str
    persistent:
      description: Defines whether the domain is persistent or transient.
      returned: success
      type: bool
    uuid:
      description: The globally unique identifier for the domain.
      returned: success
      type: str
    clock:
      description: The configuration the domain will use to synchronise it's clock from the host.
      returned: success
      type: complex
    cpu:
      description: The features and topology of the virtual CPU.
      returned: success
      type: complex
    features:
      description: The hypervisor features available to the domain.
      returned: success
      type: complex
    memory:
      description: The maximum allocation of memory for the domain at boot time.
      returned: success
      type: complex
    memory_current:
      description: The actual allocation of memory to the guest OS. Ballooning means this can be
        less than the allocation at boot time.
      returned: success
      type: complex
    memory_max:
      description: The run time maximum allocation of memory for the domain.
      returned: success
      type: complex
    os:
      description: The operating system boot configuration for the domain.
      returned: success
      type: complex
    vcpu:
      description: The maximum number of virtual CPUs allocated for the domain.
      returned: success
      type: complex
    vcpus:
      description: The state of individual virtual CPUs.
      returned: success
      type: complex
    channel:
      description: The channel devices defined for the domain.
      returned: success
      type: complex
    cdrom:
      description: The CDROM devices defined for the domain.
      returned: success
      type: complex
    disk:
      description: The disk devices defined for the domain.
      returned: success
      type: complex
    floppy:
      description: The floppy disk devices defined for the domain.
      returned: success
      type: complex
    lun:
      description: The LUN devices defined for the domain.
      returned: success
      type: complex
    filesystem:
      description: A directory on the host that can be accessed directly from the guest OS.
      returned: success
      type: complex
    graphics:
      description: The graphical devices defined for the domain.
      returned: success
      type: complex
    interface:
      description: The network interface devices defined for the domain.
      returned: success
      type: complex
    memory_device:
      description: The memory devices defined for the domain.
      returned: success
      type: complex
    video:
      description: The video devices defined for the domain.
      returned: success
      type: complex
virt_domains_live:
  description: Facts retrieved from the live domain config, with the domain name as a key. This
    contains an identical set of return values as the C(virt_domains) key.
  returned: always
  type: complex
  contains: dict
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.virt import Config, etree_to_dict, flatten_dict
from ansible.module_utils.six import string_types
import traceback

LXML_IMPORT_ERROR = None
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    LXML_IMPORT_ERROR = traceback.format_exc()
    HAS_LXML = False

LIBVIRT_IMPORT_ERROR = None
try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    LIBVIRT_IMPORT_ERROR = traceback.format_exc()
    HAS_LIBVIRT = False


class DomainConfig(Config):
    @property
    def id(self):
        return self._etree.find('.').attrib.get('id')

    @property
    def name(self):
        return self._etree.findtext('./name')

    @property
    def uuid(self):
        return self._etree.findtext('./uuid')

    @property
    def clock(self):
        return self._etree.find('./clock')

    @property
    def cpu(self):
        return self._etree.find('./cpu')

    @property
    def emulator(self):
        return self._etree.find('./devices/emulator')

    @property
    def features(self):
        return self._etree.find('./features')

    @property
    def memory(self):
        return self._etree.find('./memory')

    @property
    def memory_current(self):
        # if "currentMemory" is not defined libvirt defaults to this being equal to "memory"
        current = self._etree.find('./currentMemory')
        return self.memory if current is None else current

    @property
    def memory_max(self):
        return self._etree.find('./maxMemory')

    @property
    def os(self):
        return self._etree.find('./os')

    @property
    def vcpu(self):
        return self._etree.find('./vcpu')

    @property
    def vcpus(self):
        return self._etree.find('./vcpus')

    @property
    def channel(self):
        return self._etree.findall('.//devices/channel')

    @property
    def cdrom(self):
        return self._etree.findall(".//devices/disk[@device='cdrom']")

    @property
    def disk(self):
        return self._etree.findall(".//devices/disk[@device='disk']")

    @property
    def floppy(self):
        return self._etree.findall(".//devices/disk[@device='floppy']")

    @property
    def lun(self):
        return self._etree.findall(".//devices/disk[@device='lun']")

    @property
    def filesystem(self):
        return self._etree.findall('.//devices/filesystem')

    @property
    def graphics(self):
        return self._etree.findall('.//devices/graphics')

    @property
    def interface(self):
        return self._etree.findall('.//devices/interface')

    @property
    def memory_device(self):
        return self._etree.findall('.//devices/memory')

    @property
    def video(self):
        return self._etree.findall('.//devices/video')


def get_facts(config, wanted, domain_stats):
    facts = dict()
    for key in wanted:
        config_item = getattr(config, key)
        if isinstance(config_item, string_types) or isinstance(config_item, int):
            facts[key] = config_item
        elif isinstance(config_item, list):
            new_items = list()
            for item in config_item:
                if isinstance(item, etree._Element):
                    item_value = list(etree_to_dict(item).values())[0]
                    if isinstance(item_value, dict):
                        flat_dict = flatten_dict(item_value)
                        if key == 'disk':
                            # The "domain stats" include information about the size and usage of qcow2
                            # (and maybe other) disk images. Merge the relevant items here by matching
                            # the image file path to find the correct "block".
                            block = ''
                            for stats_key, stats_value in domain_stats.items():
                                if stats_value == flat_dict.get('source_file', None):
                                    # TODO wont match after more than 10 disk "blocks"
                                    # the format of the domain stats dict keys are "block.0.<statname>"
                                    block = stats_key[:8]
                                else:
                                    continue

                            if block + 'allocation' in domain_stats:
                                flat_dict['source_allocation'] = domain_stats[block + 'allocation']
                            if block + 'capacity' in domain_stats:
                                flat_dict['source_capacity'] = domain_stats[block + 'capacity']
                            if block + 'physical' in domain_stats:
                                flat_dict['source_physical'] = domain_stats[block + 'physical']

                        new_items.append(flat_dict)
                    else:
                        new_items.append(item_value)
                else:
                    raise TypeError('Unexpected type when reading config property list.')
            facts[key] = new_items
        elif isinstance(config_item, etree._Element):
            key_value = list(etree_to_dict(config_item).values())[0]
            facts[key] = flatten_dict(key_value) if isinstance(key_value, dict) else key_value
        else:
            facts[key] = None
    return facts


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
    domains = list()
    module = AnsibleModule(module_args, supports_check_mode=True)
    name = module.params['name']

    if not HAS_LXML:
        module.fail_json(msg=missing_required_lib('lxml'), exception=LXML_IMPORT_ERROR)

    if not HAS_LIBVIRT:
        module.fail_json(msg=missing_required_lib('libvirt'), exception=LIBVIRT_IMPORT_ERROR)

    try:
        host = libvirt.open(module.params['uri'])
        try:
            if name is not None and isinstance(name, list):
                domains = [host.lookupByName(item) for item in name]
            else:
                domains = host.listAllDomains(
                    libvirt.VIR_CONNECT_LIST_DOMAINS_PERSISTENT |
                    libvirt.VIR_CONNECT_LIST_DOMAINS_TRANSIENT
                )
        except libvirt.libvirtError as e:
            module.fail_json(msg='Domain(s) not found on this host.')

        wanted_properties = [
            'emulator', 'id', 'name', 'uuid', 'clock', 'cpu', 'features', 'memory',
            'memory_current', 'memory_max', 'os', 'vcpu', 'vcpus', 'channel', 'cdrom', 'disk',
            'floppy', 'lun', 'filesystem', 'graphics', 'interface', 'memory_device', 'video'
        ]

        for domain in domains:
            if domain.isPersistent():
                config_file = DomainConfig(module, domain.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE))
                autostart = True if domain.autostart() else False

                if domain.isActive():
                    config_live = DomainConfig(module, domain.XMLDesc())
                    active = True
            else:
                # a transient domain only has a "live" configuration
                config_live = DomainConfig(module, domain.XMLDesc())
                active = True
                persistent = False

            domain_stats = host.domainListGetStats((domain,), 255)[0][1]

            if config_file:
                facts_file[config_file.name] = get_facts(config_file, wanted_properties, domain_stats)
                facts_file[config_file.name]['active'] = active
                facts_file[config_file.name]['autostart'] = autostart
                facts_file[config_file.name]['persistent'] = persistent

            if config_live:
                facts_live[config_live.name] = get_facts(config_live, wanted_properties, domain_stats)
                facts_live[config_live.name]['active'] = active
                facts_live[config_live.name]['autostart'] = autostart
                facts_live[config_live.name]['persistent'] = persistent

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                virt_domains=facts_file if len(facts_file) > 0 else None,
                virt_domains_live=facts_live if len(facts_live) > 0 else None,
            ),
        )

    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        if host is not None:
            host.close()


if __name__ == '__main__':
    main()
