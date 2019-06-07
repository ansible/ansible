from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: aws_ssm
    plugin_type: inventory
    author:
      - Andrew Hibbert <andrew_hibbert@hotmail.com>
    requirements:
    - boto3
    - botocore
    short_description: AWS SSM inventory source
    description:
      - Fetch parameters via path
      - Add groups, hosts and variables based on path
    options:
      plugin:
        description: token that ensures this is a source file for the 'aws_ssm' plugin.
        required: True
        choices: ['aws_ssm']
      path:
        description: Path to search for in ssm
        required: True
      region:
        description: Region to retrieve SSM parameter from
        required: True
      decrypt:
        description: Whether to decrypt secrets or not
        required: False
        default: True
    extends_documentation_fragment:
        - inventory_cache
        - constructed
        - aws_credentials
'''

EXAMPLES = '''
plugin: aws_ssm
path: prod
region: us-east-1
aws_profile: default
'''

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, boto3_inventory_conn
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.utils.display import Display

try:
    import boto3  # noqa
    import botocore
except ImportError:
    raise AnsibleError("The ssm dynamic inventory plugin requires boto3 and "
                       "botocore")


display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'aws_ssm'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.credentials = {}

    def verify_file(self, path):
        ''' Verify plugin configuration file. '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('aws_ssm.yml', 'aws_ssm.yaml')):
                return True
        display.debug("aws_ssm inventory filename must end with 'aws_ssm.yml' "
                      "or 'aws_ssm.yaml'")
        return False

    def parse(self, inventory, loader, path, cache=True):
        ''' Retrieve data '''
        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        cache_key = self._get_cache_prefix(path)
        self.setup(cache, cache_key)

    def setup(self, cache, cache_key):
        ''' Retrieve parameters from config file and fetch data. '''
        decrypt = True

        path = self.get_option('path')
        region = self.get_option('region')
        if isinstance(self.get_option('decrypt'), bool):
            decrypt = self.get_option('decrypt')

        if not path or not region:
            raise AnsibleError('path and region should be present')

        client = self.get_client()

        source_data = None
        if cache and cache_key in self._cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            self.fetch_data(client, path, decrypt)

    def get_client(self):
        ''' Connect to AWS and return client to use with SSM. '''

        boto_profile = self.get_option('aws_profile')
        region = self.get_option('region')
        aws_access_key_id = self.get_option('aws_access_key')
        aws_secret_access_key = self.get_option('aws_secret_key')
        aws_security_token = self.get_option('aws_security_token')

        if aws_access_key_id:
            self.credentials['aws_access_key_id'] = aws_access_key_id
        if aws_secret_access_key:
            self.credentials['aws_secret_access_key'] = aws_secret_access_key
        if aws_security_token:
            self.credentials['aws_session_token'] = aws_security_token
        if boto_profile:
            self.credentials['profile_name'] = boto_profile

        try:
            client = boto3_inventory_conn('client', 'ssm', region, **self.credentials)
        except (botocore.exceptions.ProfileNotFound,
                botocore.exceptions.PartialCredentialsError) as e:
            raise AnsibleError("Insufficient boto credentials found: {0}".
                               format(to_native(e)))

        return client

    def fetch_data(self, client, path, decrypt):
        ''' Fetch and process all data so it is viewable in inventory. '''
        parameters = self.get_all_parameters(client, path, decrypt)
        for parameter in parameters:
            for name, value in parameter.items():
                path_list = list(filter(None, name.split('/')))
                len_path = len(path_list) - 1
                if len_path < 3:
                    display.vvvv("Ignoring {0} SSM parameter, must have a "
                                 "depth of 3 to be used with plugin "
                                 "e.g. /search/group/host/variable"
                                 .format(name))
                for index, (current, previous) in enumerate(
                        zip(path_list[1:], path_list), 1):
                    if index == 1:
                        self.inventory.add_group("all")
                        self.inventory.add_group(current)
                        self.inventory.add_child("all", current)
                    elif index == (len_path - 1):
                        self.inventory.add_host(current)
                        self.inventory.add_child(previous, current)
                    elif index == len_path:
                        formatted_variable = self.format_variable(value)
                        self.inventory.set_variable(previous,
                                                    current,
                                                    formatted_variable)
                    else:
                        self.inventory.add_group(current)
                        self.inventory.add_child(previous, current)

    def get_all_parameters(self, client, path, decrypt):
        ''' Get all parameters that match the top level path recursively '''
        ''' and return list of dicts. '''
        ret = []
        response = client.get_parameters_by_path(
            Path="/{0}".format(path),
            Recursive=True,
            WithDecryption=decrypt,
        )
        paramlist = list()
        paramlist.extend(response['Parameters'])

        while 'NextToken' in response:
            response = client.get_parameters_by_path(
                NextToken=response['NextToken'],
                Path="/{0}".format(path),
                Recursive=True,
                WithDecryption=decrypt
            )
            paramlist.extend(response['Parameters'])

        if len(paramlist):
            ret.append(boto3_tag_list_to_ansible_dict(
                       paramlist,
                       tag_name_key_name="Name",
                       tag_value_key_name="Value"))
        else:
            ret.append({})

        return ret

    def format_variable(self, value):
        ''' Check if commas in value assume StringList and return list. '''
        if len(list(filter(None, value.split(',')))) > 1:
            formatted_variable = list(filter(None, value.split(',')))
        else:
            formatted_variable = value

        return formatted_variable
