# -*- coding: utf-8 -*-

# Copyright 2017 Sloane Hertel <shertel@redhat.com>
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import datetime

# Just to test that we have the prerequisite for InventoryModule and instance_data_filter_to_boto_attr
boto3 = pytest.importorskip('boto3')
botocore = pytest.importorskip('botocore')

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory.aws_ec2 import InventoryModule
from ansible.plugins.inventory.aws_ec2 import instance_data_filter_to_boto_attr

instances = {
    u'Instances': [
        {u'Monitoring': {u'State': 'disabled'},
         u'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
         u'State': {u'Code': 16, u'Name': 'running'},
         u'EbsOptimized': False,
         u'LaunchTime': datetime.datetime(2017, 10, 31, 12, 59, 25),
         u'PublicIpAddress': '12.345.67.890',
         u'PrivateIpAddress': '098.76.54.321',
         u'ProductCodes': [],
         u'VpcId': 'vpc-12345678',
         u'StateTransitionReason': '',
         u'InstanceId': 'i-00000000000000000',
         u'EnaSupport': True,
         u'ImageId': 'ami-12345678',
         u'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
         u'KeyName': 'testkey',
         u'SecurityGroups': [{u'GroupName': 'default', u'GroupId': 'sg-12345678'}],
         u'ClientToken': '',
         u'SubnetId': 'subnet-12345678',
         u'InstanceType': 't2.micro',
         u'NetworkInterfaces': [
            {u'Status': 'in-use',
             u'MacAddress': '12:a0:50:42:3d:a4',
             u'SourceDestCheck': True,
             u'VpcId': 'vpc-12345678',
             u'Description': '',
             u'NetworkInterfaceId': 'eni-12345678',
             u'PrivateIpAddresses': [
                 {u'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
                  u'PrivateIpAddress': '098.76.54.321',
                  u'Primary': True,
                  u'Association':
                      {u'PublicIp': '12.345.67.890',
                       u'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
                       u'IpOwnerId': 'amazon'}}],
             u'PrivateDnsName': 'ip-098-76-54-321.ec2.internal',
             u'Attachment':
                 {u'Status': 'attached',
                  u'DeviceIndex': 0,
                  u'DeleteOnTermination': True,
                  u'AttachmentId': 'eni-attach-12345678',
                  u'AttachTime': datetime.datetime(2017, 10, 31, 12, 59, 25)},
             u'Groups': [
                 {u'GroupName': 'default',
                  u'GroupId': 'sg-12345678'}],
             u'Ipv6Addresses': [],
             u'OwnerId': '123456789000',
             u'PrivateIpAddress': '098.76.54.321',
             u'SubnetId': 'subnet-12345678',
             u'Association':
                {u'PublicIp': '12.345.67.890',
                 u'PublicDnsName': 'ec2-12-345-67-890.compute-1.amazonaws.com',
                 u'IpOwnerId': 'amazon'}}],
         u'SourceDestCheck': True,
         u'Placement':
            {u'Tenancy': 'default',
             u'GroupName': '',
             u'AvailabilityZone': 'us-east-1c'},
         u'Hypervisor': 'xen',
         u'BlockDeviceMappings': [
            {u'DeviceName': '/dev/xvda',
             u'Ebs':
                {u'Status': 'attached',
                 u'DeleteOnTermination': True,
                 u'VolumeId': 'vol-01234567890000000',
                 u'AttachTime': datetime.datetime(2017, 10, 31, 12, 59, 26)}}],
         u'Architecture': 'x86_64',
         u'RootDeviceType': 'ebs',
         u'RootDeviceName': '/dev/xvda',
         u'VirtualizationType': 'hvm',
         u'Tags': [{u'Value': 'test', u'Key': 'ansible'}, {u'Value': 'aws_ec2', u'Key': 'name'}],
         u'AmiLaunchIndex': 0}],
    u'ReservationId': 'r-01234567890000000',
    u'Groups': [],
    u'OwnerId': '123456789000'
}


@pytest.fixture(scope="module")
def inventory():
    return InventoryModule()


def test_compile_values(inventory):
    found_value = instances['Instances'][0]
    chain_of_keys = instance_data_filter_to_boto_attr['instance.group-id']
    for attr in chain_of_keys:
        found_value = inventory._compile_values(found_value, attr)
    assert found_value == "sg-12345678"


def test_get_boto_attr_chain(inventory):
    instance = instances['Instances'][0]
    assert inventory._get_boto_attr_chain('network-interface.addresses.private-ip-address', instance) == "098.76.54.321"


def test_boto3_conn(inventory):
    inventory._options = {"boto_profile": "first_precedence",
                          "aws_access_key_id": "test_access_key",
                          "aws_secret_access_key": "test_secret_key",
                          "aws_security_token": "test_security_token"}
    inventory._set_credentials()
    with pytest.raises(AnsibleError) as error_message:
        for connection, region in inventory._boto3_conn(regions=['us-east-1']):
            assert error_message == "Insufficient credentials found."


def test_get_hostname_default(inventory):
    instance = instances['Instances'][0]
    assert inventory._get_hostname(instance, hostnames=None) == "ec2-12-345-67-890.compute-1.amazonaws.com"


def test_get_hostname(inventory):
    hostnames = ['ip-address', 'dns-name']
    instance = instances['Instances'][0]
    assert inventory._get_hostname(instance, hostnames) == "12.345.67.890"


def test_set_credentials(inventory):
    inventory._options = {'aws_access_key_id': 'test_access_key',
                          'aws_secret_access_key': 'test_secret_key',
                          'aws_security_token': 'test_security_token',
                          'boto_profile': 'test_profile'}
    inventory._set_credentials()

    assert inventory.boto_profile == "test_profile"
    assert inventory.aws_access_key_id == "test_access_key"
    assert inventory.aws_secret_access_key == "test_secret_key"
    assert inventory.aws_security_token == "test_security_token"


def test_insufficient_credentials(inventory):
    inventory._options = {
        'aws_access_key_id': None,
        'aws_secret_access_key': None,
        'aws_security_token': None,
        'boto_profile': None
    }
    with pytest.raises(AnsibleError) as error_message:
        inventory._set_credentials()
        assert "Insufficient boto credentials found" in error_message


def test_validate_option(inventory):
    assert ['us-east-1'] == inventory._validate_option('regions', list, 'us-east-1')
    assert ['us-east-1'] == inventory._validate_option('regions', list, ['us-east-1'])


def test_illegal_option(inventory):
    bad_filters = [{'tag:Environment': 'dev'}]
    with pytest.raises(AnsibleParserError) as error_message:
        inventory._validate_option('filters', dict, bad_filters)
        assert "The option filters ([{'tag:Environment': 'dev'}]) must be a <class 'dict'>" == error_message


def test_empty_config_query_options(inventory):
    regions, filters, hostnames, strict_permissions = inventory._get_query_options({})
    assert regions == filters == hostnames == []
    assert strict_permissions is True


def test_conig_query_options(inventory):
    regions, filters, hostnames, strict_permissions = inventory._get_query_options(
        {'regions': ['us-east-1', 'us-east-2'],
         'filters': {'tag:Environment': ['dev', 'prod']},
         'hostnames': 'ip-address',
         'strict_permissions': False}
    )
    assert regions == ['us-east-1', 'us-east-2']
    assert filters == [{'Name': 'tag:Environment', 'Values': ['dev', 'prod']}]
    assert hostnames == ['ip-address']
    assert strict_permissions is False


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('not_aws_config.yml') is False
