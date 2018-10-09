#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import pytest


@pytest.fixture
def ec2_inventory():
    # contrib's dirstruct doesn't contain __init__.py files
    # import ec2 inventory manually
    inventory_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 'contrib',
            'inventory'))
    sys.path.append(inventory_dir)

    try:
        ec2 = pytest.importorskip('ec2')
    finally:
        # cleanup so that path is not polluted with other scripts
        sys.path.remove(inventory_dir)

    return ec2


@pytest.fixture
def mock_euca(mocker):
    regionMock = mocker.MagicMock()
    regionMock.name = 'us-gov-west-1'
    m = mocker.MagicMock(region=regionMock)

    return m


@pytest.fixture
def mock_regions(mocker):
    mock1 = mocker.MagicMock()
    mock1.name = 'ap-northest-1'
    mock2 = mocker.MagicMock()
    mock2.name = 'us-east-1'
    mock3 = mocker.MagicMock()
    mock3.name = 'us-gov-west-1'
    mock4 = mocker.MagicMock()
    mock4.name = 'cn-north-1'

    return [
        mock1,
        mock2,
        mock3,
        mock4,
    ]


@pytest.fixture
def mock_ec2_regions_call(mocker, mock_regions, ec2_inventory):
    return mocker.patch('ec2.ec2.regions',
                        mocker.MagicMock(return_value=mock_regions))


@pytest.fixture
def mock_connect_euca_call(mocker, mock_euca, ec2_inventory):
    return mocker.patch('ec2.boto.connect_euca',
                        mocker.MagicMock(return_value=mock_euca))


def test_read_regions_setting_no_regions_option_no_eucalyptus(
        mock_ec2_regions_call, ec2_inventory):
    eucalyptus = False
    eucalyptus_host = []
    credentials = {}

    # only use comma
    config_regions = 'ap-northest-1,us-east-1,us-gov-west-1,cn-north-1'
    config_regions_exclude = 'us-east-1,us-gov-west-1'
    args_regions = None
    expected = ['ap-northest-1', 'cn-north-1']
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual

    # mix space and comma
    config_regions = 'ap-northest-1,  us-east-1,  us-gov-west-1,cn-north-1'
    config_regions_exclude = 'us-east-1, us-gov-west-1'
    args_regions = None
    expected = ['ap-northest-1', 'cn-north-1']
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual

    config_regions = 'all'
    config_regions_exclude = 'us-east-1, us-gov-west-1'
    args_regions = None
    expected = ['ap-northest-1', 'cn-north-1']

    with mock_ec2_regions_call:
        actual = ec2_inventory.Ec2Inventory._read_regions_setting(
            eucalyptus, eucalyptus_host, credentials, args_regions,
            config_regions, config_regions_exclude)
    assert expected == actual

    config_regions = 'auto'
    config_regions_exclude = 'us-east-1, us-gov-west-1'
    args_regions = None
    expected = ['cn-north-1']
    os.environ['AWS_REGION'] = 'cn-north-1'
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual
    del os.environ['AWS_REGION']

    config_regions = 'auto'
    config_regions_exclude = 'us-gov-west-1'
    args_regions = None
    expected = ['us-east-1']
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual
    del os.environ['AWS_DEFAULT_REGION']


def test_read_regions_setting_with_regions_option_no_eucalyptus(ec2_inventory):
    eucalyptus = False
    eucalyptus_host = []
    credentials = {}

    # only use comma
    config_regions = 'will skip this setting'
    config_regions_exclude = 'us-east-1,us-gov-west-1'
    args_regions = 'us-east-1,us-gov-west-1,cn-north-1'
    expected = ['cn-north-1']
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual

    # mix space and comma
    config_regions = 'will skip this setting'
    config_regions_exclude = 'us-east-1,us-gov-west-1'
    args_regions = 'us-east-1,  us-gov-west-1,cn-north-1'
    expected = ['cn-north-1']
    actual = ec2_inventory.Ec2Inventory._read_regions_setting(
        eucalyptus, eucalyptus_host, credentials, args_regions, config_regions,
        config_regions_exclude)
    assert expected == actual


def test_read_regions_setting_no_regions_option_with_eucalyptus(
        mock_connect_euca_call, ec2_inventory):
    eucalyptus = True
    eucalyptus_host = ['ad-hoc']
    credentials = {'key': 'value'}

    config_regions = 'all'
    config_regions_exclude = 'us-east-1'
    args_regions = None
    expected = ['us-gov-west-1']
    with mock_connect_euca_call:
        actual = ec2_inventory.Ec2Inventory._read_regions_setting(
            eucalyptus, eucalyptus_host, credentials, args_regions,
            config_regions, config_regions_exclude)
    assert expected == actual
