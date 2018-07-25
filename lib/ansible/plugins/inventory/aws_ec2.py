# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: aws_ec2
    plugin_type: inventory
    short_description: ec2 inventory source
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from Amazon Web Services EC2.
        - Uses a <name>.aws_ec2.yaml (or <name>.aws_ec2.yml) YAML configuration file.
    options:
        plugin:
            description: token that ensures this is a source file for the 'aws_ec2' plugin.
            required: True
            choices: ['aws_ec2']
        boto_profile:
          description: The boto profile to use.
          env:
              - name: AWS_PROFILE
              - name: AWS_DEFAULT_PROFILE
        aws_access_key_id:
          description: The AWS access key to use. If you have specified a profile, you don't need to provide
              an access key/secret key/session token.
          env:
              - name: AWS_ACCESS_KEY_ID
              - name: AWS_ACCESS_KEY
              - name: EC2_ACCESS_KEY
        aws_secret_access_key:
          description: The AWS secret key that corresponds to the access key. If you have specified a profile,
              you don't need to provide an access key/secret key/session token.
          env:
              - name: AWS_SECRET_ACCESS_KEY
              - name: AWS_SECRET_KEY
              - name: EC2_SECRET_KEY
        aws_security_token:
          description: The AWS security token if using temporary access and secret keys.
          env:
              - name: AWS_SECURITY_TOKEN
              - name: AWS_SESSION_TOKEN
              - name: EC2_SECURITY_TOKEN
        regions:
          description: A list of regions in which to describe EC2 instances. By default this is all regions except us-gov-west-1
              and cn-north-1.
        hostnames:
          description: A list in order of precedence for hostname variables. You can use the options specified in
              U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options). To use tags as hostnames
              use the syntax tag:Name=Value to use the hostname Name_Value, or tag:Name to use the value of the Name tag.
        filters:
          description: A dictionary of filter value pairs. Available filters are listed here
              U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options)
        strict_permissions:
          description: By default if a 403 (Forbidden) is encountered this plugin will fail. You can set strict_permissions to
              False in the inventory config file which will allow 403 errors to be gracefully skipped.
'''

EXAMPLES = '''

# Minimal example using environment vars or instance role credentials
# Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address
plugin: aws_ec2
regions:
  - us-east-1

# Example using filters, ignoring permission errors, and specifying the hostname precedence
plugin: aws_ec2
boto_profile: aws_profile
regions: # populate inventory with instances in these regions
  - us-east-1
  - us-east-2
filters:
  # all instances with their `Environment` tag set to `dev`
  tag:Environment: dev
  # all dev and QA hosts
  tag:Environment:
    - dev
    - qa
  instance.group-id: sg-xxxxxxxx
# ignores 403 errors rather than failing
strict_permissions: False
# note: I(hostnames) sets the inventory_hostname. To modify ansible_host without modifying
# inventory_hostname use compose (see example below).
hostnames:
  - tag:Name=Tag1,Name=Tag2  # return specific hosts only
  - tag:CustomDNSName
  - dns-name
  - private-ip-address

# Example using constructed features to create groups and set ansible_host
plugin: aws_ec2
regions:
  - us-east-1
  - us-west-1
# keyed_groups may be used to create custom groups
strict: False
keyed_groups:
  # add e.g. x86_64 hosts to an arch_x86_64 group
  - prefix: arch
    key: 'architecture'
  # add hosts to tag_Name_Value groups for each Name/Value tag pair
  - prefix: tag
    key: tags
  # add hosts to e.g. instance_type_z3_tiny
  - prefix: instance_type
    key: instance_type
  # create security_groups_sg_abcd1234 group for each SG
  - key: 'security_groups|json_query("[].group_id")'
    prefix: 'security_groups'
  # create a group for each value of the Application tag
  - key: tags.Application
    separator: ''
  # create a group per region e.g. aws_region_us_east_2
  - key: placement.region
    prefix: aws_region
# set individual variables with compose
compose:
  # use the private IP address to connect to the host
  # (note: this does not modify inventory_hostname, which is set via I(hostnames))
  ansible_host: private_ip_address
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


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


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'aws_ec2'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.group_prefix = 'aws_ec2_'

        # credentials
        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None

    def _compile_values(self, obj, attr):
        '''
            :param obj: A list or dict of instance attributes
            :param attr: A key
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
            :param instance: instance dict returned by boto3 ec2 describe_instances()
        '''
        allowed_filters = sorted(list(instance_data_filter_to_boto_attr.keys()) + list(instance_meta_filter_to_boto_attr.keys()))
        if filter_name not in allowed_filters:
            raise AnsibleError("Invalid filter '%s' provided; filter must be one of %s." % (filter_name,
                                                                                            allowed_filters))
        if filter_name in instance_data_filter_to_boto_attr:
            boto_attr_list = instance_data_filter_to_boto_attr[filter_name]
        else:
            boto_attr_list = instance_meta_filter_to_boto_attr[filter_name]

        instance_value = instance
        for attribute in boto_attr_list:
            instance_value = self._compile_values(instance_value, attribute)
        return instance_value

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
                        raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
                else:
                    raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
            yield connection, region

    def _get_instances_by_region(self, regions, filters, strict_permissions):
        '''
           :param regions: a list of regions in which to describe instances
           :param filters: a list of boto3 filter dicionaries
           :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
           :return A list of instance dictionaries
        '''
        all_instances = []

        for connection, region in self._boto3_conn(regions):
            try:
                # By default find non-terminated/terminating instances
                if not any([f['Name'] == 'instance-state-name' for f in filters]):
                    filters.append({'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopping', 'stopped']})
                paginator = connection.get_paginator('describe_instances')
                reservations = paginator.paginate(Filters=filters).build_full_result().get('Reservations')
                instances = []
                for r in reservations:
                    instances.extend(r.get('Instances'))
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == 403 and not strict_permissions:
                    instances = []
                else:
                    raise AnsibleError("Failed to describe instances: %s" % to_native(e))
            except botocore.exceptions.BotoCoreError as e:
                raise AnsibleError("Failed to describe instances: %s" % to_native(e))

            all_instances.extend(instances)

        return sorted(all_instances, key=lambda x: x['InstanceId'])

    def _get_tag_hostname(self, preference, instance):
        tag_hostnames = preference.split('tag:', 1)[1]
        if ',' in tag_hostnames:
            tag_hostnames = tag_hostnames.split(',')
        else:
            tag_hostnames = [tag_hostnames]
        tags = boto3_tag_list_to_ansible_dict(instance.get('Tags', []))
        for v in tag_hostnames:
            if '=' in v:
                tag_name, tag_value = v.split('=')
                if tags.get(tag_name) == tag_value:
                    return to_text(tag_name) + "_" + to_text(tag_value)
            else:
                tag_value = tags.get(v)
                if tag_value:
                    return to_text(tag_value)
        return None

    def _get_hostname(self, instance, hostnames):
        '''
            :param instance: an instance dict returned by boto3 ec2 describe_instances()
            :param hostnames: a list of hostname destination variables in order of preference
            :return the preferred identifer for the host
        '''
        if not hostnames:
            hostnames = ['dns-name', 'private-dns-name']

        hostname = None
        for preference in hostnames:
            if 'tag' in preference:
                if not preference.startswith('tag:'):
                    raise AnsibleError("To name a host by tags name_value, use 'tag:name=value'.")
                hostname = self._get_tag_hostname(preference, instance)
            else:
                hostname = self._get_boto_attr_chain(preference, instance)
            if hostname:
                break
        if hostname:
            if ':' in to_text(hostname):
                return to_safe_group_name(to_text(hostname))
            else:
                return to_text(hostname)

    def _query(self, regions, filters, strict_permissions):
        '''
            :param regions: a list of regions to query
            :param filters: a list of boto3 filter dictionaries
            :param hostnames: a list of hostname destination variables in order of preference
            :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
        '''
        return {'aws_ec2': self._get_instances_by_region(regions, filters, strict_permissions)}

    def _populate(self, groups, hostnames):
        for group in groups:
            self.inventory.add_group(group)
            self._add_hosts(hosts=groups[group], group=group, hostnames=hostnames)
            self.inventory.add_child('all', group)

    def _populate_from_source(self, source_data):
        hostvars = source_data.pop('_meta', {}).get('hostvars', {})
        for group in source_data:
            if group == 'all':
                continue
            else:
                self.inventory.add_group(group)
                hosts = source_data[group].get('hosts', [])
                for host in hosts:
                    self._populate_host_vars([host], hostvars.get(host, {}), group)
                self.inventory.add_child('all', group)

    def _format_inventory(self, groups, hostnames):
        results = {'_meta': {'hostvars': {}}}
        for group in groups:
            results[group] = {'hosts': []}
            for host in groups[group]:
                hostname = self._get_hostname(host, hostnames)
                if not hostname:
                    continue
                results[group]['hosts'].append(hostname)
                h = self.inventory.get_host(hostname)
                results['_meta']['hostvars'][h.name] = h.vars
        return results

    def _add_hosts(self, hosts, group, hostnames):
        '''
            :param hosts: a list of hosts to be added to a group
            :param group: the name of the group to which the hosts belong
            :param hostnames: a list of hostname destination variables in order of preference
        '''
        for host in hosts:
            hostname = self._get_hostname(host, hostnames)

            host = camel_dict_to_snake_dict(host, ignore_list=['Tags'])
            host['tags'] = boto3_tag_list_to_ansible_dict(host.get('tags', []))

            # Allow easier grouping by region
            host['placement']['region'] = host['placement']['availability_zone'][:-1]

            if not hostname:
                continue
            self.inventory.add_host(hostname, group=group)
            for hostvar, hostval in host.items():
                self.inventory.set_variable(hostname, hostvar, hostval)

            # Use constructed if applicable

            strict = self.get_option('strict')

            # Composed variables
            self._set_composite_vars(self.get_option('compose'), host, hostname, strict=strict)

            # Complex groups based on jinaj2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option('groups'), host, hostname, strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname, strict=strict)

    def _set_credentials(self):
        '''
            :param config_data: contents of the inventory config file
        '''

        self.boto_profile = self.get_option('boto_profile')
        self.aws_access_key_id = self.get_option('aws_access_key_id')
        self.aws_secret_access_key = self.get_option('aws_secret_access_key')
        self.aws_security_token = self.get_option('aws_security_token')

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            session = botocore.session.get_session()
            if session.get_credentials() is not None:
                self.aws_access_key_id = session.get_credentials().access_key
                self.aws_secret_access_key = session.get_credentials().secret_key
                self.aws_security_token = session.get_credentials().token

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            raise AnsibleError("Insufficient boto credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.aws_ec2.yml') or path.endswith('.aws_ec2.yaml'):
                return True
        display.debug("aws_ec2 inventory filename must end with '*.aws_ec2.yml' or '*.aws_ec2.yaml'")
        return False

    def _get_query_options(self, config_data):
        '''
            :param config_data: contents of the inventory config file
            :return A list of regions to query,
                    a list of boto3 filter dicts,
                    a list of possible hostnames in order of preference
                    a boolean to indicate whether to fail on permission errors
        '''
        options = {'regions': {'type_to_be': list, 'value': config_data.get('regions', [])},
                   'filters': {'type_to_be': dict, 'value': config_data.get('filters', {})},
                   'hostnames': {'type_to_be': list, 'value': config_data.get('hostnames', [])},
                   'strict_permissions': {'type_to_be': bool, 'value': config_data.get('strict_permissions', True)}}

        # validate the options
        for name in options:
            options[name]['value'] = self._validate_option(name, options[name]['type_to_be'], options[name]['value'])

        regions = options['regions']['value']
        filters = ansible_dict_to_boto3_filter_list(options['filters']['value'])
        hostnames = options['hostnames']['value']
        strict_permissions = options['strict_permissions']['value']

        return regions, filters, hostnames, strict_permissions

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

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._read_config_data(path)
        self._set_credentials()

        # get user specifications
        regions, filters, hostnames, strict_permissions = self._get_query_options(config_data)

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option('cache')

        # Generate inventory
        formatted_inventory = {}
        cache_needs_update = False
        if cache:
            try:
                results = self.cache.get(cache_key)
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True
            else:
                self._populate_from_source(results)

        if not cache or cache_needs_update:
            results = self._query(regions, filters, strict_permissions)
            self._populate(results, hostnames)
            formatted_inventory = self._format_inventory(results, hostnames)

        # If the cache has expired/doesn't exist or if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option('cache')):
            self.cache.set(cache_key, formatted_inventory)
