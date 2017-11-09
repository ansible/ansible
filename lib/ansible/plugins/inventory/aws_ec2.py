# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: aws_ec2
    plugin_type: inventory
    short_description: ec2 inventory source
    description:
        - Get inventory hosts from Amazon Web Services EC2.
        - Uses a <name>.aws_ec2.yaml (or <name>.aws_ec2.yml) YAML configuration file.
    options:
        boto_profile:
          description: The boto profile to use. If not provided, the environment variables AWS_PROFILE and AWS_DEFAULT_PROFILE
              will be checked.
        aws_access_key_id:
          description: The AWS access key to use. If not provided, the environment variables AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY,
              and EC2_ACCESS_KEY will be checked. If you have specified a profile, you don't need to provide
              an access key/secret key/session token.
        aws_secret_key_id:
          description: The AWS secret key that corresponds to the access key. If not provided, the environment variables
              AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, and EC2_SECRET_KEY will be checked. If you have specified a profile,
              you don't need to provide an access key/secret key/session token.
        aws_security_token:
          description: The AWS security token if using temporary access and secret keys. If not provided in the config file, the
              environment variables AWS_SECURITY_TOKEN, AWS_SESSION_TOKEN, EC2_SECURITY_TOKEN will be checked.
              If you have specified a profile, you don't need to provide an access key/secret key/session token.
        regions:
          description: A list of regions in which to describe EC2 instances. By default this is all regions except us-gov-west-1
              and cn-north-1.
        hostnames:
          description: A list in order of precedence for hostname variables. You can use any of the options specified in
              U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options.)
        filters:
          description: A dictionary of filter value pairs. Available filters are listed here
              U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options)
        group_by:
          description: A list of filters (and optionally their values) to create inventory groups with. Available filters are
              listed here U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options)
        strict_permissions:
          description: By default if a 403 (Forbidden) is encountered this plugin will fail. You can set strict_permissions to
              False in the inventory config file which will allow 403 errors to be gracefully skipped.
'''

EXAMPLES = '''
simple_config_file:
    plugin: aws_ec2
    boto_profile: aws_profile
    regions: # populate inventory with instances in these regions
      - us-east-1
      - us-east-2
    group_by:
    # makes a group for instances that have the tag key 'name' and value 'value'
      - tag:name=value
    # makes a group for instances that have the tag key 'prod' regardless of the value
      - tag-key=prod
    # makes a group for instances that have the tag values 'test' and 'ansible' regardless of the tag keys
      - tag-value=test,ansible
      - instance-type=t2.micro
      - state
    filters:
    # filter by tags with the value dev
      tag:Name: dev
      instance.group-id: sg-xxxxxxxx
    # ignores 403 errors rather than failing
    strict_permissions: False
'''

from ansible.plugins.inventory import BaseInventoryPlugin, to_safe_group_name
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict
from collections import namedtuple

import os

try:
    import boto3
    import botocore
except ImportError:
    raise AnsibleError('The ec2 dynamic inventory plugin requires boto3 and botocore.')

# The mappings give an array of keys to get from the filter name to the value
# returned by boto3's EC2 describe_instances method.

instance_meta_filter_to_boto_attr = {
    'group-id': ('Groups', 'GroupId'),
    'group-name': ('Groups', 'GroupName'),
    'network-interface.attachment.instance-owner-id': ('OwnerId',),
    'owner-id': ('OwnerId',),
    'requester-id': ('RequesterId',),
    'reservation-id': ('ReservationId',),
}

instance_data_filter_to_boto_attr = {
    'affinity': ('Placement', 'Affinity'),
    'architecture': ('Architecture',),
    'availability-zone': ('Placement', 'AvailabilityZone'),
    'block-device-mapping.attach-time': ('BlockDeviceMappings', 'Ebs', 'AttachTime'),
    'block-device-mapping.delete-on-termination': ('BlockDeviceMappings', 'Ebs', 'DeleteOnTermination'),
    'block-device-mapping.device-name': ('BlockDeviceMappings', 'DeviceName'),
    'block-device-mapping.status': ('BlockDeviceMappings', 'Ebs', 'Status'),
    'block-device-mapping.volume-id': ('BlockDeviceMappings', 'Ebs', 'VolumeId'),
    'client-token': ('ClientToken',),
    'dns-name': ('PublicDnsName',),
    'host-id': ('Placement', 'HostId'),
    'hypervisor': ('Hypervisor',),
    'iam-instance-profile.arn': ('IamInstanceProfile', 'Arn'),
    'image-id': ('ImageId',),
    'instance-id': ('InstanceId',),
    'instance-lifecycle': ('InstanceLifecycle',),
    'instance-state-code': ('State', 'Code'),
    'instance-state-name': ('State', 'Name'),
    'instance-type': ('InstanceType',),
    'instance.group-id': ('SecurityGroups', 'GroupId'),
    'instance.group-name': ('SecurityGroups', 'GroupName'),
    'ip-address': ('PublicIpAddress',),
    'kernel-id': ('KernelId',),
    'key-name': ('KeyName',),
    'launch-index': ('AmiLaunchIndex',),
    'launch-time': ('LaunchTime',),
    'monitoring-state': ('Monitoring', 'State'),
    'network-interface.addresses.private-ip-address': ('NetworkInterfaces', 'PrivateIpAddress'),
    'network-interface.addresses.primary': ('NetworkInterfaces', 'PrivateIpAddresses', 'Primary'),
    'network-interface.addresses.association.public-ip': ('NetworkInterfaces', 'PrivateIpAddresses', 'Association', 'PublicIp'),
    'network-interface.addresses.association.ip-owner-id': ('NetworkInterfaces', 'PrivateIpAddresses', 'Association', 'IpOwnerId'),
    'network-interface.association.public-ip': ('NetworkInterfaces', 'Association', 'PublicIp'),
    'network-interface.association.ip-owner-id': ('NetworkInterfaces', 'Association', 'IpOwnerId'),
    'network-interface.association.allocation-id': ('ElasticGpuAssociations', 'ElasticGpuId'),
    'network-interface.association.association-id': ('ElasticGpuAssociations', 'ElasticGpuAssociationId'),
    'network-interface.attachment.attachment-id': ('NetworkInterfaces', 'Attachment', 'AttachmentId'),
    'network-interface.attachment.instance-id': ('InstanceId',),
    'network-interface.attachment.device-index': ('NetworkInterfaces', 'Attachment', 'DeviceIndex'),
    'network-interface.attachment.status': ('NetworkInterfaces', 'Attachment', 'Status'),
    'network-interface.attachment.attach-time': ('NetworkInterfaces', 'Attachment', 'AttachTime'),
    'network-interface.attachment.delete-on-termination': ('NetworkInterfaces', 'Attachment', 'DeleteOnTermination'),
    'network-interface.availability-zone': ('Placement', 'AvailabilityZone'),
    'network-interface.description': ('NetworkInterfaces', 'Description'),
    'network-interface.group-id': ('NetworkInterfaces', 'Groups', 'GroupId'),
    'network-interface.group-name': ('NetworkInterfaces', 'Groups', 'GroupName'),
    'network-interface.ipv6-addresses.ipv6-address': ('NetworkInterfaces', 'Ipv6Addresses', 'Ipv6Address'),
    'network-interface.mac-address': ('NetworkInterfaces', 'MacAddress'),
    'network-interface.network-interface-id': ('NetworkInterfaces', 'NetworkInterfaceId'),
    'network-interface.owner-id': ('NetworkInterfaces', 'OwnerId'),
    'network-interface.private-dns-name': ('NetworkInterfaces', 'PrivateDnsName'),
    # 'network-interface.requester-id': (),
    'network-interface.requester-managed': ('NetworkInterfaces', 'Association', 'IpOwnerId'),
    'network-interface.status': ('NetworkInterfaces', 'Status'),
    'network-interface.source-dest-check': ('NetworkInterfaces', 'SourceDestCheck'),
    'network-interface.subnet-id': ('NetworkInterfaces', 'SubnetId'),
    'network-interface.vpc-id': ('NetworkInterfaces', 'VpcId'),
    'placement-group-name': ('Placement', 'GroupName'),
    'platform': ('Platform',),
    'private-dns-name': ('PrivateDnsName',),
    'private-ip-address': ('PrivateIpAddress',),
    'product-code': ('ProductCodes', 'ProductCodeId'),
    'product-code.type': ('ProductCodes', 'ProductCodeType'),
    'ramdisk-id': ('RamdiskId',),
    'reason': ('StateTransitionReason',),
    'root-device-name': ('RootDeviceName',),
    'root-device-type': ('RootDeviceType',),
    'source-dest-check': ('SourceDestCheck',),
    'spot-instance-request-id': ('SpotInstanceRequestId',),
    'state-reason-code': ('StateReason', 'Code'),
    'state-reason-message': ('StateReason', 'Message'),
    'subnet-id': ('SubnetId',),
    'tag': ('Tags',),
    'tag-key': ('Tags',),
    'tag-value': ('Tags',),
    'tenancy': ('Placement', 'Tenancy'),
    'virtualization-type': ('VirtualizationType',),
    'vpc-id': ('VpcId',),
}


class InventoryModule(BaseInventoryPlugin):

    NAME = 'aws_ec2'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.group_prefix = 'aws_ec2_'

        # configuration
        self.cache = None
        self.do_cache = False
        self.cache_timeout = 0
        self.cache_path = None

        # credentials
        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None

    def _get_group_by_tag_values(self, group, instance):
        '''
            :param group: The instance attribute to group by
            :param instance: A named tuple of the instance data retrieved by boto3 describe_instances
            :return A list of tag keys or tag values or a dict of key:value pairs
        '''
        tags = boto3_tag_list_to_ansible_dict(instance.instance_data.get('Tags', []))
        if group.startswith('tag:'):
            return tags
        elif group.startswith('tag-key'):
            return list(tags.keys())
        elif group.startswith('tag-value'):
            return list(tags.values())
        else:
            raise AnsibleError("To group by tags, use 'tag:name=value', 'tag-value=value', or 'tag-key=key'")

    def _get_group_by_values(self, group, instance):
        '''
            :param group: The instance attribute to group by
            :param instance: a namedtuple of the instance data retrieved by boto3 describe_instances
            :return The value of the instance's group attribute.
        '''
        if 'tag' in group:
            return self._get_group_by_tag_values(group, instance)
        return self._get_boto_attr_chain(group, instance)

    def _compile_values(self, obj, attr):
        '''
            :param obj: A list or dict of instance attributes
            :param attr: An index or key
            :return The value(s) found via the attr
        '''
        if obj is None:
            return

        temp_obj = []

        if isinstance(obj, list) or isinstance(obj, tuple):
            for each in obj:
                value = self._compile_values(each, attr)
                if value:
                    temp_obj.append(value)
        else:
            temp_obj = obj.get(attr)

        has_indexes = any([isinstance(temp_obj, list), isinstance(temp_obj, tuple)])
        if has_indexes and len(temp_obj) == 1:
            return temp_obj[0]

        return temp_obj

    def _get_boto_attr_chain(self, filter_name, instance):
        '''
            :param filter_name: The filter
            :param instance: A namedtuple
        '''
        allowed_filters = sorted(list(instance_data_filter_to_boto_attr.keys()) + list(instance_meta_filter_to_boto_attr.keys()))
        if filter_name not in allowed_filters:
            raise AnsibleError("Invalid filter provided. %s must be one of %s." % (filter_name,
                                                                                   allowed_filters))
        if filter_name in instance_data_filter_to_boto_attr:
            boto_attr_list = instance_data_filter_to_boto_attr[filter_name]
            instance_value = instance.instance_data
        else:
            boto_attr_list = instance_meta_filter_to_boto_attr[filter_name]
            instance_value = instance.instance_meta

        for attribute in boto_attr_list:
            instance_value = self._compile_values(instance_value, attribute)
        return instance_value

    def _get_group_by_name_and_value(self, group_by):
        '''
            :param group_by A list of filters (and optional corresponding values)
            :return The group_by name and the group_by value (if one is provided)
        '''
        if not group_by:
            yield 'aws_ec2', None

        for group in group_by:
            if group.startswith('tag:'):
                group_name = 'tag:'
                group_value = group.split('tag:', 1)[1]
            elif '=' in group:
                group_name, group_value = group.split('=')
            else:
                group_name, group_value = group, 'all'
            yield group_name, group_value

    def _compare_tag_groupings(self, group_value, found_value):
        '''
            :param group_value The tags defining a group (a list of tag keys or tag values or a dict of key:values)
            :param found_value The tags associated with an instance (a list or dictionary that corresponds to group_value)
            :return boolean, whether or not the group_value and found_value are the same
        '''
        if isinstance(group_value, string_types):
            tags = group_value.split(',')

            if isinstance(found_value, list):
                if set(sorted(tags)) <= set(sorted(found_value)):
                    return True
            elif isinstance(found_value, dict):
                if not found_value:
                    return False

                format_tags = {}

                # no specified value; check each key is in the found value dict
                if any('=' not in tag for tag in tags):
                    return set([key for key, value in self._get_group_by_name_and_value(tags)]).issubset(set(list(found_value)))

                # a specified value; check the specified dict matches or is a subset of the found one
                for key, value in self._get_group_by_name_and_value(tags):
                    format_tags[key] = value
                return set(format_tags.items()).issubset(set(found_value.items()))

    def _assemble_groups(self, instances, group_by_name):
        '''
            :param instances: A list of namedtuples
            :param group_by_name: A list of group_bys provided in the inventory config file
            :return A dictionary of groups of dictionaries of group value(s) mapping to instances

            Example of a return data structure:

            {'instance-type': {'t2.micro': [<class 'ansible.plugins.inventory.ec2.instance'>]}}
        '''
        groups = {}

        for group_name, group_value in self._get_group_by_name_and_value(group_by_name):
            groups[group_name] = groups.get(group_name) or {}


            if group_name == 'aws_ec2' and group_value is None:
                groups['aws_ec2'] = instances
                continue

            for instance in instances:
                found_value = self._get_group_by_values(group_name, instance)

                if group_value != 'all' and not (group_name == 'tag:' and '=' not in group_value):
                    groups[group_name][group_value] = groups[group_name].get(group_value) or []
                    if 'tag' in group_name and self._compare_tag_groupings(group_value, found_value):
                        groups[group_name][group_value].append(instance)
                    elif found_value == group_value:
                        groups[group_name][group_value].append(instance)
                    elif group_value in found_value:
                        groups[group_name][group_value].append(instance)
                else:
                    # group by all values for the given attribute
                    if 'tag:' == group_name:
                        if self._compare_tag_groupings(group_value, found_value):
                            for key, value in found_value.items():
                                tag_key_value = "%s_%s" % (key, value)
                                groups[group_name][tag_key_value] = groups[group_name].get(tag_key_value) or []
                                groups[group_name][tag_key_value].append(instance)
                    elif isinstance(found_value, list):
                        for value in found_value:
                            groups[group_name][value] = groups[group_name].get(value) or []
                            groups[group_name][value].append(instance)
                    elif found_value is not None:
                        groups[group_name][found_value] = groups[group_name].get(found_value) or []
                        groups[group_name][found_value].append(instance)
        return groups

    def _get_credentials(self):
        '''
            :return A dictionary of boto client credentials
        '''

        boto_params = {}
        for credential in (('aws_access_key_id', self.aws_access_key_id),
                           ('aws_secret_access_key', self.aws_secret_access_key),
                           ('aws_session_token', self.aws_security_token)):
            if credential[1]:
                boto_params[credential[0]] = credential[1]

        return boto_params

    def _boto3_conn(self, regions):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''

        credentials = self._get_credentials()

        for region in regions:
            try:
                connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region, **credentials)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                if self.boto_profile:
                    try:
                        connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region)
                    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                        raise AnsibleError("Insufficient credentials found.")
                else:
                    raise AnsibleError("Insufficient credentials found.")
            yield connection, region

    def _format_instance_data(self, region, instances):
        '''
            :param region: the region in which the instance exists
            :param instances: the reservations returned by boto3's describe_instances

            A generator that yields named tuples with the fields region, instance_meta, and instance_data.
        '''
        instance_meta = {'Groups': instances.get('Groups', []),
                         'OwnerId': instances.get('OwnerId'),
                         'RequesterId': instances.get('RequesterId'),
                         'ReservationId': instances.get('ReservationId')}
        for instance_data in instances.get('Instances', []):
            instance = namedtuple('instance', ['region', 'instance_meta', 'instance_data'])
            instance.region = region
            instance.instance_meta = instance_meta
            instance.instance_data = instance_data
            yield instance

    def _get_instances_by_region(self, regions, filters, strict_permissions):
        '''
           :param regions: a list of regions in which to describe instances
           :param filters: a list of boto3 filter dicionaries
           :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
           :return A list of namedtuples containing the fields region, instance_meta, and instance_data
        '''
        all_instances = []

        for connection, region in self._boto3_conn(regions):
            try:
                paginator = connection.get_paginator('describe_instances')
                instances = paginator.paginate(Filters=filters).build_full_result().get('Reservations')
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == 403 and not strict_permissions:
                    instances = []
                else:
                    raise AnsibleError("Failed to describe instances: %s" % to_native(e))
            except botocore.exceptions.BotoCoreError as e:
                raise AnsibleError("Failed to describe instances: %s" % to_native(e))

            for instance in instances:
                all_instances.extend(self._format_instance_data(region, instance))

        return sorted(all_instances, key=lambda x: x.instance_data['InstanceId'])

    def _get_hostname(self, instance, hostnames):
        '''
            :param instance: a named tuple with instance_data field
            :param hostnames: a list of hostname destination variables in order of preference
            :return the preferred identifer for the host
        '''
        if not hostnames:
            hostnames = ['dns-name', 'private-dns-name']

        for preference in hostnames:
            hostname = self._get_boto_attr_chain(preference, instance)
            if hostname:
                if ':' in to_text(hostname):
                    return to_safe_group_name(to_text(hostname))
                else:
                    return to_text(hostname)

    def _populate(self, regions, filters, group_by, hostnames, strict_permissions):
        '''
            :param regions: a list of regions to query
            :param filters: a list of boto3 filter dictionaries
            :param group_by: a list of filters to group the query results
            :param hostnames: a list of hostname destination variables in order of preference
            :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
        '''
        filtered_instances = self._get_instances_by_region(regions, filters, strict_permissions)
        groups = self._assemble_groups(filtered_instances, group_by)

        for group_n in groups:
            if group_n == 'aws_ec2':
                self.inventory.add_group(group_n)
                self._add_hosts(hosts=groups[group_n], group=group_n, hostnames=hostnames)
            else:
                for group_v in groups[group_n]:
                    if group_n == 'tag:':
                        groupname = to_safe_group_name(self.group_prefix + to_text(group_n) + to_text(group_v))
                    else:
                        groupname = to_safe_group_name(self.group_prefix + to_text(group_n) + '_' + to_text(group_v))
                    self.inventory.add_group(groupname)
                    self._add_hosts(hosts=groups[group_n][group_v], group=groupname, hostnames=hostnames)

    def _add_hosts(self, hosts, group, hostnames):
        '''
            :param hosts: a list of hosts to be added to a group
            :param group: the name of the group to which the hosts belong
            :param hostnames: a list of hostname destination variables in order of preference
        '''
        for host in hosts:
            hostname = self._get_hostname(host, hostnames)
            self.inventory.add_host(hostname, group=group)
            for hostvar in host.instance_data.keys():
                self.inventory.set_variable(hostname, hostvar, host.instance_data[hostvar])

    def _find_cred(self, possible_env_vars):
        '''
            :param possible_env_vars: the possible environment variables to check for a credential
        '''
        for env_var in possible_env_vars:
            if os.environ.get(env_var):
                return os.environ.get(env_var)

    def _set_credentials(self, config_data):
        '''
            :param config_data: contents of the inventory config file
        '''

        self.boto_profile = config_data.get('boto_profile')
        self.aws_access_key_id = config_data.get('aws_access_key_id')
        self.aws_secret_access_key = config_data.get('aws_secret_access_key')
        self.aws_security_token = config_data.get('aws_security_token')

        if not self.boto_profile:
            self.boto_profile = self._find_cred(possible_env_vars=('AWS_PROFILE',
                                                                   'AWS_DEFAULT_PROFILE'))

        if not self.aws_access_key_id:
            self.aws_access_key_id = self._find_cred(possible_env_vars=('AWS_ACCESS_KEY_ID',
                                                                        'AWS_ACCESS_KEY',
                                                                        'EC2_ACCESS_KEY'))

        if not self.aws_secret_access_key:
            self.aws_secret_access_key = self._find_cred(possible_env_vars=('AWS_SECRET_ACCESS_KEY',
                                                                            'AWS_SECRET_KEY',
                                                                            'EC2_SECRET_KEY'))

        if not self.aws_security_token:
            self.aws_security_token = self._find_cred(possible_env_vars=('AWS_SECURITY_TOKEN',
                                                                         'AWS_SESSION_TOKEN',
                                                                         'EC2_SECURITY_TOKEN'))
        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            raise AnsibleError("Insufficient boto credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

    def _validate_config(self, loader, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        self.verify_file(path)

        # file is config file
        try:
            config_data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError(to_native(e))

        if not config_data or config_data.get('plugin') != self.NAME:
            # this is not my config file
            raise AnsibleParserError("Not a ec2 inventory plugin configuration file")

        return config_data

    def _set_cache(self, inventory, path):
        '''
            :param inventory: an ansible.inventory.data.InventoryData object
            :param path: the path to the inventory config file
        '''
        cache_key = self.get_cache_prefix(path)
        if cache_key not in inventory.cache:
            inventory.cache[cache_key] = {}
        self.cache = inventory.cache[cache_key]

    def _get_query_options(self, config_data):
        '''
            :param config_data: contents of the inventory config file
            :return A list of region strings,
                    a list of boto3 filter dicts,
                    a list of inventory groups,
                    a list of possible hostnames in order of preference
                    a boolean to indicate whether to fail on permission errors
        '''
        options = {'regions': {'type_to_be': list, 'value': config_data.get('regions', [])},
                   'filters': {'type_to_be': dict, 'value': config_data.get('filters', {})},
                   'group_by': {'type_to_be': list, 'value': config_data.get('group_by', [])},
                   'hostnames': {'type_to_be': list, 'value': config_data.get('hostnames', [])},
                   'strict_permissions': {'type_to_be': bool, 'value': config_data.get('strict_permissions', True)}}

        # validate the options
        for name in options:
            options[name]['value'] = self._validate_option(name, options[name]['type_to_be'], options[name]['value'])

        regions = options['regions']['value']
        filters = ansible_dict_to_boto3_filter_list(options['filters']['value'])
        group_by = options['group_by']['value']
        hostnames = options['hostnames']['value']
        strict_permissions = options['strict_permissions']['value']

        return regions, filters, group_by, hostnames, strict_permissions

    def _validate_option(self, name, desired_type, option_value):
        '''
            :param name: the option name
            :param desired_type: the class the option needs to be
            :param option: the value the user has provided
            :return The option of the correct class
        '''

        if isinstance(option_value, string_types) and desired_type == list:
            option_value = [option_value]

        if option_value is None:
            option_value = desired_type()

        if not isinstance(option_value, desired_type):
            raise AnsibleParserError("The option %s (%s) must be a %s" % (name, option_value, desired_type))

        return option_value

    def verify_file(self, path):
        '''
            :param path: the path to the inventory config file
            :return True if the config file has a valid name
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.aws_ec2.yml' or '.aws_ec2.yaml'):
                return True

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._validate_config(loader, path)

        self._set_cache(inventory, path)
        self._set_credentials(config_data)

        # get user specifications
        regions, filters, group_by, hostnames, strict_permissions = self._get_query_options(config_data)

        # actually populate inventory
        self._populate(regions, filters, group_by, hostnames, strict_permissions)
