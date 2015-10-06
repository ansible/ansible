#!/usr/bin/python -tt
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
module: xenserver_facts
version_added: "2.0"
short_description: get facts reported on xenserver
description:
  - Reads data out of XenAPI, can be used instead of multiple xe commands.
author:
    - Andy Hill (@andyhky)
    - Tim Rupp
'''

import platform
import XenAPI

EXAMPLES = '''
- name: Gather facts from xenserver
   xenserver:

- name: Print running VMs
  debug: msg="{{ item }}"
  with_items: xs_vms.keys()
  when: xs_vms[item]['power_state'] == "Running"

TASK: [Print running VMs] ***********************************************************
skipping: [10.13.0.22] => (item=CentOS 4.7 (32-bit))
ok: [10.13.0.22] => (item=Control domain on host: 10.0.13.22) => {
    "item": "Control domain on host: 10.0.13.22",
    "msg": "Control domain on host: 10.0.13.22"
}
'''

class XenServerFacts:
    def __init__(self):
        self.codes = {
            '5.5.0': 'george',
            '5.6.100': 'oxford',
            '6.0.0': 'boston',
            '6.1.0': 'tampa',
            '6.2.0': 'clearwater'
        }

    @property
    def version(self):
        # Be aware! Deprecated in Python 2.6!
        result = platform.dist()[1]
        return result

    @property
    def codename(self):
        if self.version in self.codes:
            result = self.codes[self.version]
        else:
            result = None

        return result


def get_xenapi_session():
    session = XenAPI.xapi_local()
    session.xenapi.login_with_password('', '')
    return session


def get_networks(session):
    recs = session.xenapi.network.get_all_records()
    xs_networks = {}
    networks = change_keys(recs, key='uuid')
    for network in networks.itervalues():
        xs_networks[network['name_label']] = network
    return xs_networks


def get_pifs(session):
    recs = session.xenapi.PIF.get_all_records()
    pifs = change_keys(recs, key='uuid')
    xs_pifs = {}
    devicenums = range(0, 7)
    for pif in pifs.itervalues():
        for eth in devicenums:
            interface_name = "eth%s" % (eth)
            bond_name = interface_name.replace('eth', 'bond')
            if pif['device'] == interface_name:
                xs_pifs[interface_name] = pif
            elif pif['device'] == bond_name:
                xs_pifs[bond_name] = pif
    return xs_pifs


def get_vlans(session):
    recs = session.xenapi.VLAN.get_all_records()
    return change_keys(recs, key='tag')


def change_keys(recs, key='uuid', filter_func=None):
    """
    Take a xapi dict, and make the keys the value of recs[ref][key].

    Preserves the ref in rec['ref']

    """
    new_recs = {}

    for ref, rec in recs.iteritems():
        if filter_func is not None and not filter_func(rec):
            continue

        new_recs[rec[key]] = rec
        new_recs[rec[key]]['ref'] = ref

    return new_recs

def get_host(session):
    """Get the host"""
    host_recs = session.xenapi.host.get_all()
    # We only have one host, so just return its entry
    return session.xenapi.host.get_record(host_recs[0])

def get_vms(session):
    xs_vms = {}
    recs = session.xenapi.VM.get_all()
    if not recs:
        return None

    vms = change_keys(recs, key='uuid')
    for vm in vms.itervalues():
       xs_vms[vm['name_label']] = vm
    return xs_vms


def get_srs(session):
    xs_srs = {}
    recs = session.xenapi.SR.get_all()
    if not recs:
        return None
    srs = change_keys(recs, key='uuid')
    for sr in srs.itervalues():
       xs_srs[sr['name_label']] = sr
    return xs_srs

def main():
    module = AnsibleModule({})

    obj = XenServerFacts()
    try:
        session = get_xenapi_session()
    except XenAPI.Failure, e:
        module.fail_json(msg='%s' % e)

    data = {
        'xenserver_version': obj.version,
        'xenserver_codename': obj.codename
    }

    xs_networks = get_networks(session)
    xs_pifs = get_pifs(session)
    xs_vlans = get_vlans(session)
    xs_vms = get_vms(session)
    xs_srs = get_srs(session)

    if xs_vlans:
        data['xs_vlans'] = xs_vlans
    if xs_pifs:
        data['xs_pifs'] = xs_pifs
    if xs_networks:
        data['xs_networks'] = xs_networks

    if xs_vms:
        data['xs_vms'] = xs_vms

    if xs_srs:
        data['xs_srs'] = xs_srs

    module.exit_json(ansible=data)

from ansible.module_utils.basic import *

main()
