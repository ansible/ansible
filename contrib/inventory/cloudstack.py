#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible,
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

######################################################################

"""
Ansible CloudStack external inventory script.
=============================================

Generates Ansible inventory from CloudStack. Configuration is read from
'cloudstack.ini'. If you need to pass the project, write a simple wrapper
script, e.g. project_cloudstack.sh:

  #!/bin/bash
  cloudstack.py --project <your_project> $@


When run against a specific host, this script returns the following attributes
based on the data obtained from CloudStack API:

  "web01": {
    "cpu_number": 2,
    "nic": [
      {
        "ip": "10.102.76.98",
        "mac": "02:00:50:99:00:01",
        "type": "Isolated",
        "netmask": "255.255.255.0",
        "gateway": "10.102.76.1"
      },
      {
        "ip": "10.102.138.63",
        "mac": "06:b7:5a:00:14:84",
        "type": "Shared",
        "netmask": "255.255.255.0",
        "gateway": "10.102.138.1"
      }
    ],
    "default_ip": "10.102.76.98",
    "zone": "ZUERICH",
    "created": "2014-07-02T07:53:50+0200",
    "hypervisor": "VMware",
    "memory": 2048,
    "state": "Running",
    "tags": [],
    "cpu_speed": 1800,
    "affinity_group": [],
    "service_offering": "Small",
    "cpu_used": "62%"
  }


usage: cloudstack.py [--list] [--host HOST] [--project PROJECT]  [--domain DOMAIN]
"""

from __future__ import print_function

import sys
import argparse

try:
    import json
except:
    import simplejson as json


try:
    from cs import CloudStack, CloudStackException, read_config
except ImportError:
    print("Error: CloudStack library must be installed: pip install cs.",
          file=sys.stderr)
    sys.exit(1)


class CloudStackInventory(object):
    def __init__(self):

        parser = argparse.ArgumentParser()
        parser.add_argument('--host')
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--tag', help="Filter machines by a tag. Should be in the form key=value.")
        parser.add_argument('--project')
        parser.add_argument('--domain')

        options = parser.parse_args()
        try:
            self.cs = CloudStack(**read_config())
        except CloudStackException:
            print("Error: Could not connect to CloudStack API", file=sys.stderr)

        domain_id = None
        if options.domain:
            domain_id = self.get_domain_id(options.domain)

        project_id = None
        if options.project:
            project_id = self.get_project_id(options.project, domain_id)

        if options.host:
            data = self.get_host(options.host, project_id, domain_id)
            print(json.dumps(data, indent=2))

        elif options.list:
            tags = dict()
            if options.tag:
                tags['tags[0].key'], tags['tags[0].value'] = options.tag.split('=')
            data = self.get_list(project_id, domain_id, **tags)
            print(json.dumps(data, indent=2))
        else:
            print("usage: --list [--tag <tag>] | --host <hostname> [--project <project>] [--domain <domain_path>]",
                  file=sys.stderr)
            sys.exit(1)

    def get_domain_id(self, domain):
        domains = self.cs.listDomains(listall=True)
        if domains:
            for d in domains['domain']:
                if d['path'].lower() == domain.lower():
                    return d['id']
        print("Error: Domain %s not found." % domain, file=sys.stderr)
        sys.exit(1)

    def get_project_id(self, project, domain_id=None):
        projects = self.cs.listProjects(domainid=domain_id)
        if projects:
            for p in projects['project']:
                if p['name'] == project or p['id'] == project:
                    return p['id']
        print("Error: Project %s not found." % project, file=sys.stderr)
        sys.exit(1)

    def get_host(self, name, project_id=None, domain_id=None, **kwargs):
        hosts = self.cs.listVirtualMachines(projectid=project_id, domainid=domain_id, fetch_list=True, **kwargs)
        data = {}
        if not hosts:
            return data
        for host in hosts:
            host_name = host['displayname']
            if name == host_name:
                data['zone'] = host['zonename']
                if 'group' in host:
                    data['group'] = host['group']
                data['state'] = host['state']
                data['service_offering'] = host['serviceofferingname']
                data['affinity_group'] = host['affinitygroup']
                data['security_group'] = host['securitygroup']
                data['cpu_number'] = host['cpunumber']
                data['cpu_speed'] = host['cpuspeed']
                if 'cpuused' in host:
                    data['cpu_used'] = host['cpuused']
                data['memory'] = host['memory']
                data['tags'] = host['tags']
                data['hypervisor'] = host['hypervisor']
                data['created'] = host['created']
                data['nic'] = []
                for nic in host['nic']:
                    data['nic'].append({
                        'ip': nic['ipaddress'],
                        'mac': nic['macaddress'],
                        'netmask': nic['netmask'],
                        'gateway': nic['gateway'],
                        'type': nic['type'],
                    })
                    if nic['isdefault']:
                        data['default_ip'] = nic['ipaddress']
                break
        return data

    def get_list(self, project_id=None, domain_id=None, **kwargs):
        data = {
            'all': {
                'hosts': [],
            },
            '_meta': {
                'hostvars': {},
            },
        }

        groups = self.cs.listInstanceGroups(projectid=project_id, domainid=domain_id)
        if groups:
            for group in groups['instancegroup']:
                group_name = group['name']
                if group_name and group_name not in data:
                    data[group_name] = {
                        'hosts': []
                    }

        hosts = self.cs.listVirtualMachines(projectid=project_id, domainid=domain_id, fetch_list=True, **kwargs)
        if not hosts:
            return data
        for host in hosts:
            host_name = host['displayname']
            data['all']['hosts'].append(host_name)
            data['_meta']['hostvars'][host_name] = {}

            # Make a group per zone
            data['_meta']['hostvars'][host_name]['zone'] = host['zonename']
            group_name = host['zonename']
            if group_name not in data:
                data[group_name] = {
                    'hosts': []
                }
            data[group_name]['hosts'].append(host_name)

            if 'group' in host:
                data['_meta']['hostvars'][host_name]['group'] = host['group']
            data['_meta']['hostvars'][host_name]['state'] = host['state']
            data['_meta']['hostvars'][host_name]['service_offering'] = host['serviceofferingname']
            data['_meta']['hostvars'][host_name]['affinity_group'] = host['affinitygroup']
            data['_meta']['hostvars'][host_name]['security_group'] = host['securitygroup']
            data['_meta']['hostvars'][host_name]['cpu_number'] = host['cpunumber']
            data['_meta']['hostvars'][host_name]['cpu_speed'] = host['cpuspeed']
            if 'cpuused' in host:
                data['_meta']['hostvars'][host_name]['cpu_used'] = host['cpuused']
            data['_meta']['hostvars'][host_name]['created'] = host['created']
            data['_meta']['hostvars'][host_name]['memory'] = host['memory']
            data['_meta']['hostvars'][host_name]['tags'] = host['tags']
            data['_meta']['hostvars'][host_name]['hypervisor'] = host['hypervisor']
            data['_meta']['hostvars'][host_name]['created'] = host['created']
            data['_meta']['hostvars'][host_name]['nic'] = []
            for nic in host['nic']:
                data['_meta']['hostvars'][host_name]['nic'].append({
                    'ip': nic['ipaddress'],
                    'mac': nic['macaddress'],
                    'netmask': nic['netmask'],
                    'gateway': nic['gateway'],
                    'type': nic['type'],
                })
                if nic['isdefault']:
                    data['_meta']['hostvars'][host_name]['default_ip'] = nic['ipaddress']

            group_name = ''
            if 'group' in host:
                group_name = host['group']

            if group_name and group_name in data:
                data[group_name]['hosts'].append(host_name)
        return data


if __name__ == '__main__':
    CloudStackInventory()
