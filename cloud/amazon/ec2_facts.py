#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: ec2_facts
short_description: Gathers facts about remote hosts within ec2 (aws)
version_added: "1.0"
options:
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 1.5.1
description:
     - This module fetches data from the metadata servers in ec2 (aws) as per
       http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html.
       The module must be called from within the EC2 instance itself.
notes:
    - Parameters to filter on ec2_facts may be added later.
author: "Silviu Dicu <silviudicu@gmail.com>"
'''

EXAMPLES = '''
# Conditional example
- name: Gather facts
  action: ec2_facts

- name: Conditional
  action: debug msg="This instance is a t1.micro"
  when: ansible_ec2_instance_type == "t1.micro"
'''
   
import socket
import re

socket.setdefaulttimeout(5)

class Ec2Metadata(object):

    ec2_metadata_uri = 'http://169.254.169.254/latest/meta-data/'
    ec2_sshdata_uri  = 'http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key'
    ec2_userdata_uri = 'http://169.254.169.254/latest/user-data/'

    AWS_REGIONS = ('ap-northeast-1',
                   'ap-southeast-1',
                   'ap-southeast-2',
                   'eu-central-1',
                   'eu-west-1',
                   'sa-east-1',
                   'us-east-1',
                   'us-west-1',
                   'us-west-2',
                   'us-gov-west-1'
                   )

    def __init__(self, module, ec2_metadata_uri=None, ec2_sshdata_uri=None, ec2_userdata_uri=None):
        self.module   = module
        self.uri_meta = ec2_metadata_uri or self.ec2_metadata_uri
        self.uri_user = ec2_userdata_uri or self.ec2_userdata_uri
        self.uri_ssh  =  ec2_sshdata_uri or self.ec2_sshdata_uri
        self._data     = {}
        self._prefix   = 'ansible_ec2_%s'

    def _fetch(self, url):
        (response, info) = fetch_url(self.module, url, force=True)
        if response:
            data = response.read()
        else:
            data = None
        return data

    def _mangle_fields(self, fields, uri, filter_patterns=['public-keys-0']):
        new_fields = {}
        for key, value in fields.iteritems():
            split_fields = key[len(uri):].split('/')
            if len(split_fields) > 1 and split_fields[1]:
                new_key = "-".join(split_fields)
                new_fields[self._prefix % new_key] = value
            else:
                new_key = "".join(split_fields)
                new_fields[self._prefix % new_key] = value
        for pattern in filter_patterns:
            for key in new_fields.keys():
                match = re.search(pattern, key)
                if match: 
                    new_fields.pop(key)
        return new_fields

    def fetch(self, uri, recurse=True):
        raw_subfields = self._fetch(uri)
        if not raw_subfields:
            return
        subfields = raw_subfields.split('\n')
        for field in subfields:
            if field.endswith('/') and recurse:
                self.fetch(uri + field)
            if uri.endswith('/'):
                new_uri = uri + field
            else:
                new_uri = uri + '/' + field
            if new_uri not in self._data and not new_uri.endswith('/'):
                content = self._fetch(new_uri)
                if field == 'security-groups':
                    sg_fields = ",".join(content.split('\n'))
                    self._data['%s' % (new_uri)]  = sg_fields
                else:
                    self._data['%s' % (new_uri)] = content

    def fix_invalid_varnames(self, data):
        """Change ':'' and '-' to '_' to ensure valid template variable names"""
        for (key, value) in data.items():
            if ':' in key or '-' in key:
                newkey = key.replace(':','_').replace('-','_')
                del data[key]
                data[newkey] = value

    def add_ec2_region(self, data):
        """Use the 'ansible_ec2_placement_availability_zone' key/value
        pair to add 'ansible_ec2_placement_region' key/value pair with
        the EC2 region name.
        """

        # Only add a 'ansible_ec2_placement_region' key if the
        # 'ansible_ec2_placement_availability_zone' exists.
        zone = data.get('ansible_ec2_placement_availability_zone')
        if zone is not None:
            # Use the zone name as the region name unless the zone
            # name starts with a known AWS region name.
            region = zone
            for r in self.AWS_REGIONS:
                if zone.startswith(r):
                    region = r
                    break
            data['ansible_ec2_placement_region'] = region

    def run(self):
        self.fetch(self.uri_meta) # populate _data
        data = self._mangle_fields(self._data, self.uri_meta)
        data[self._prefix % 'user-data'] = self._fetch(self.uri_user)
        data[self._prefix % 'public-key'] = self._fetch(self.uri_ssh)
        self.fix_invalid_varnames(data)
        self.add_ec2_region(data)
        return data

def main():
    argument_spec = url_argument_spec()

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode = True,
    )

    ec2_facts = Ec2Metadata(module).run()
    ec2_facts_result = dict(changed=False, ansible_facts=ec2_facts)

    module.exit_json(**ec2_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
