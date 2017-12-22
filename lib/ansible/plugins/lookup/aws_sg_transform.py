# (c) 2017, Aaron Haaf <aabonh(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import get_ec2_names_from_security_group_ids
from ansible.module_utils.ec2 import get_ec2_security_group_ids_from_names
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase

try:
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

DOCUMENTATION = '''
lookup: aws_ssm
author: Aaron Haaf <aabonh(at)gmail.com>
version_added: 2.5
short_description: Convert between name and id for AWS EC2 Security Groups
description: Changes names like "My-Group-A" to an identifier like sg-2hg21da
options:
    aws_profile:
    description: The boto profile to use. You may use environment variables or the default profile as an alternative.
    region:
    description: The region to use. You may use environment variables or the default profile's region as an alternative.
    id_to_name:
    description: Go backwards and convert identifiers to names
    default: False
'''

EXAMPLES = '''
# lookup sample:
- name: Lookup a single group
  debug: msg="{{lookup('aws_sg_transform', "MyGroupA")}}"
  #=> ['sg-A']

- name: Lookup a few groups in a different region
  debug: msg="{{lookup('aws_sg_transform', "MyGroupA", "MyGroupB", region="eu-west-1")}}"
  #=> [ ['sg-A'], ['sg-B'] ]

# Multiple groups:
- name: Get a few groups going
  set_fact:
    my_groups_a: ['MyGroupA', 'MyGroupB'] #=> ['sg-A', 'sg-B']
    my_groups_b: ['MyGroupC', 'MyGroupD'] #=> ['sg-C', 'sg-D']

- name: Look up a few groups in a different region
  debug: msg="{{lookup('aws_sg_transform', my_groups_a, 'MyGroupC', region="eu-west-1")}}"
  #=> [ ['sg-A', 'sg-B'], ['sg-C'] ]

- name: Go backwards you crazy diamond
  debug: msg="{{ lookup('aws_sg_transform', 'sg-A', id_to_name=True)}}"
  #=> ['MyGroupA']
'''


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        '''
            :param terms: a list of plugin options
                          e.g. [ [sg-A, sg-B], sg-C ]
            :param variables: variables for the current host
            :return An array of strings
        '''

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required.')

        fauxdule = self.ModuleFacade(kwargs)
        region = get_aws_connection_info(fauxdule)[0]

        if not region:
            raise AnsibleError('please specify region somehow')

        ec2 = boto3.client('ec2', region_name=region)

        results = []

        for group_list in terms:
            if boolean(kwargs.get('id_to_name')):
                # sg-... => MyName
                names = get_ec2_names_from_security_group_ids(group_list, ec2, vpc_id=kwargs.get('vpc_id'))
                results.append(names)
            else:
                # MyName => sg-...
                ids = get_ec2_security_group_ids_from_names(group_list, ec2, vpc_id=kwargs.get('vpc_id'))
                results.append(ids)

        return results


    # This is not a module, so construct something that has the same interfaceish
    class ModuleFacade(object):


        def __init__(self, kwargs):
            self.params = self.ParamMock(kwargs)


        class ParamMock(object):
            def __init__(self, incoming_dict):
                self.my_dict = incoming_dict

            def get(self, key):
                if key in self.my_dict:
                    return self.my_dict[key]

                return None
