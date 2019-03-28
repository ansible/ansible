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
version_added: "2.8"
author: Chris Redit
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
  - python >= 2.7
  - libvirt-python
'''

EXAMPLES = '''
- name: Retrieve facts for all the domains on a host
  virt_domain_facts:

- name: Retrieve facts for the domains mydomain1 and mydomain2
  virt_domain_facts: name=mydomain1,mydomain2

- name: Retrieve the MAC addresses present on all the persistent domains
  virt_domain_facts:
- debug:
    msg: "{{item.key}}: {{item.value['interface'] | map(attribute='mac_address') | join(', ')}}"
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
    uuid:
      description: The globally unique identifier for the domain.
      returned: success
      type: str
    name:
      description: The short name for the domain.
      returned: success
      type: str
    memory:
      description: The maximum allocation of memory for the domain at boot time.
      returned: success
      type: str
    memory_current:
      description: The actual allocation of memory to the guest OS. Ballooning means this can be
        less than the allocation at boot time.
      returned: success
      type: str
    cpu:
      description: The number of virtual CPUs allocated for the domain.
      returned: success
      type: str
    floppy:
      description: The floppy disk devices defined for the domain.
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
    lun:
      description: The LUN devices defined for the domain.
      returned: success
      type: complex
    interface:
      description: The network interface devices defined for the domain.
      returned: success
      type: complex
    channel:
      description: The channel devices defined for the domain.
      returned: success
      type: complex
    graphics:
      description: The graphical devices defined for the domain.
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
'''

from ansible.module_utils.basic import AnsibleModule
import xml.etree.ElementTree as etree
import ansible.module_utils.six as six
import collections
import sys
import traceback
import libvirt


class Config():
    def __init__(self, xml):
        try:
            self._etree = etree.fromstring(xml)
        except etree.ParseError as e:
            six.reraise(type(e), 'Error parsing domain XML, ' + str(e), sys.exc_info()[2])

    def __str__(self):
        return etree.tostring(self._etree, encoding='utf-8')

    @property
    def uuid(self):
        return getattr(self._etree.find('.//uuid'), 'text', None)

    @property
    def name(self):
        return getattr(self._etree.find('.//name'), 'text', None)

    @property
    def memory(self):
        return getattr(self._etree.find('.//memory'), 'text', None)

    @property
    def memory_current(self):
        current = getattr(self._etree.find('.//currentMemory'), 'text', None)
        return self.memory if current is None else current

    @property
    def cpu(self):
        return getattr(self._etree.find('.//vcpu'), 'text', None)

    @property
    def floppy(self):
        return self._etree.findall(".//disk[@device='floppy']")

    @property
    def cdrom(self):
        return self._etree.findall(".//disk[@device='cdrom']")

    @property
    def disk(self):
        return self._etree.findall(".//disk[@device='disk']")

    @property
    def lun(self):
        return self._etree.findall(".//disk[@device='lun']")

    @property
    def interface(self):
        return self._etree.findall(".//interface")

    @property
    def channel(self):
        return self._etree.findall(".//channel")

    @property
    def graphics(self):
        return self._etree.findall(".//graphics")

    @property
    def video(self):
        return self._etree.findall(".//video")


def etree_to_dict(element):
    parent = {element.tag: {} if element.attrib else None}
    children = list(element)
    if children:
        # create default dict using a list to deal with duplicate tags
        dd = collections.defaultdict(list)
        for child in map(etree_to_dict, children):
            for k, v in child.items():
                # Append each child item to the list in the defaultdict, duplicate tags also get
                # appended to the list.
                dd[k].append(v)
        # Add the child dicts to the parent, the one item lists have the only value added,
        # otherwise the whole list is added representing multiple elements with the same tag.
        parent = {element.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if element.attrib:
        parent[element.tag].update(('@' + k, v) for k, v in element.attrib.items())
    if element.text:
        text = element.text.strip()
        if children or element.attrib:
            if text:
                parent[element.tag]['#text'] = text
        else:
            parent[element.tag] = text
    return parent


def flatten_dict(d, parent_key='', seperator='_'):
    items = list()
    for k, v in d.items():
        # modify some of the key names to make the flattened key cleaner
        if k == '#text':
            new_key = parent_key if parent_key else k
        elif k[:1] == '@':
            new_key = parent_key + seperator + k[1:] if parent_key else k[1:]
        else:
            new_key = parent_key + seperator + k if parent_key else k

        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, seperator=seperator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_facts(config, domain_stats):
    # the properties of the Config object we want to include in the facts
    wanted = [
        'uuid', 'name', 'memory', 'memory_current', 'cpu', 'floppy', 'cdrom', 'disk', 'lun',
        'interface', 'channel', 'graphics', 'video'
    ]
    facts = dict()

    for key in wanted:
        config_item = getattr(config, key)
        if isinstance(config_item, six.string_types) or isinstance(config_item, int):
            facts[key] = config_item
        elif isinstance(config_item, list):
            new_items = list()
            for item in config_item:
                if isinstance(item, etree.Element):
                    # The first key in the output from etree_to_dict is the tag name for the
                    # current element. This is not required as we use the propery name from the
                    # Config object. So only get the value here.
                    item_dict = flatten_dict(list(six.viewvalues(etree_to_dict(item)))[0])
                    if key == 'disk':
                        # The "domain stats" include information about the size and usage of
                        # qcow2 (and maybe other) disk images. Merge the relevant items here
                        # by matching the image path.
                        item_key = ''
                        for domain_key, domain_value in domain_stats.items():
                            if domain_value == item_dict.get('source_file', None):
                                # the format of the domain stats dict keys are "block.0.<name>"
                                item_key = domain_key[:8]
                            else:
                                continue

                        if item_key + 'allocation' in domain_stats:
                            item_dict['source_allocation'] = domain_stats[item_key + 'allocation']
                        if item_key + 'capacity' in domain_stats:
                            item_dict['source_capacity'] = domain_stats[item_key + 'capacity']
                        if item_key + 'physical' in domain_stats:
                            item_dict['source_physical'] = domain_stats[item_key + 'physical']

                    new_items.append(item_dict)
                else:
                    raise TypeError('Unexpected type when reading config property list.')
            facts[key] = new_items
        elif isinstance(config_item, etree.Element):
            facts[key] = flatten_dict(etree_to_dict(config_item))
        else:
            raise TypeError('Unexpected type when reading config property.')
    return facts


def main():
    module_args = dict(
        name=dict(type='list'),
        uri=dict(type='str', default='qemu:///system'),
    )

    host = None
    config_live = None
    config_file = None
    facts_file = dict()
    facts_live = dict()
    domains = list()
    module = AnsibleModule(module_args)
    name = module.params['name']

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

        for domain in domains:
            if domain.isPersistent():
                config_file = Config(
                    domain.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
                )
                if domain.isActive():
                    config_live = Config(domain.XMLDesc())
            else:
                # a transient domain only has a "live" configuration
                config_live = Config(domain.XMLDesc())

            domain_stats = host.domainListGetStats((domain,), 255)[0][1]
            if config_file:
                facts_file[config_file.name] = get_facts(config_file, domain_stats)

            if config_live:
                facts_live[config_live.name] = get_facts(config_live, domain_stats)

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
