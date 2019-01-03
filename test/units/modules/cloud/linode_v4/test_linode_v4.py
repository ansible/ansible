from __future__ import (absolute_import, division, print_function)

import json
import os
import sys

import pytest

linode_apiv4 = pytest.importorskip('linode_api4')
mandatory_py_version = pytest.mark.skipif(
    sys.version_info < (2, 7),
    reason='The linode_api4 dependency requires python2.7 or higher'
)

from linode_api4.errors import ApiError as LinodeApiError
from linode_api4 import LinodeClient

from ansible.modules.cloud.linode import linode_v4
from ansible.module_utils.linode import get_user_agent
from units.modules.utils import set_module_args
from units.compat import mock


def test_mandatory_state_is_validated(capfd):
    with pytest.raises(SystemExit):
        set_module_args({'label': 'foo'})
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert all(txt in results['msg'] for txt in ('state', 'required'))
    assert results['failed'] is True


def test_mandatory_label_is_validated(capfd):
    with pytest.raises(SystemExit):
        set_module_args({'state': 'present'})
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert all(txt in results['msg'] for txt in ('label', 'required'))
    assert results['failed'] is True


def test_mandatory_access_token_is_validated(default_args,
                                             no_access_token_in_env,
                                             capfd):
    with pytest.raises(SystemExit):
        set_module_args(default_args)
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['failed'] is True
    assert all(txt in results['msg'] for txt in (
        'missing',
        'required',
        'access_token',
    ))


def test_mandatory_access_token_passed_in_env(default_args,
                                              access_token):
    set_module_args(default_args)

    try:
        module = linode_v4.initialise_module()
    except SystemExit:
        pytest.fail("'access_token' is passed in environment")

    now_set_token = module.params['access_token']
    assert now_set_token == os.environ['LINODE_ACCESS_TOKEN']


def test_mandatory_access_token_passed_in_as_parameter(default_args,
                                                       no_access_token_in_env):
    default_args.update({'access_token': 'foo'})
    set_module_args(default_args)

    try:
        module = linode_v4.initialise_module()
    except SystemExit:
        pytest.fail("'access_token' is passed in as parameter")

    assert module.params['access_token'] == 'foo'


def test_instance_by_label_cannot_authenticate(capfd, access_token,
                                               default_args):
    set_module_args(default_args)
    module = linode_v4.initialise_module()
    client = LinodeClient(module.params['access_token'])

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, side_effect=LinodeApiError('foo')):
        with pytest.raises(SystemExit):
            linode_v4.maybe_instance_from_label(module, client)

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['failed'] is True
    assert 'Unable to query the Linode API' in results['msg']


def test_no_instances_found_with_label_gives_none(default_args,
                                                  access_token):
    set_module_args(default_args)
    module = linode_v4.initialise_module()
    client = LinodeClient(module.params['access_token'])

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[]):
        result = linode_v4.maybe_instance_from_label(module, client)

    assert result is None


def test_optional_region_is_validated(default_args, capfd, access_token):
    default_args.update({'type': 'foo', 'image': 'bar'})
    set_module_args(default_args)

    with pytest.raises(SystemExit):
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['failed'] is True
    assert all(txt in results['msg'] for txt in (
        'required',
        'together',
        'region'
    ))


def test_optional_type_is_validated(default_args, capfd, access_token):
    default_args.update({'region': 'foo', 'image': 'bar'})
    set_module_args(default_args)

    with pytest.raises(SystemExit):
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['failed'] is True
    assert all(txt in results['msg'] for txt in (
        'required',
        'together',
        'type'
    ))


def test_optional_image_is_validated(default_args, capfd, access_token):
    default_args.update({'type': 'foo', 'region': 'bar'})
    set_module_args(default_args)

    with pytest.raises(SystemExit):
        linode_v4.initialise_module()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['failed'] is True
    assert all(txt in results['msg'] for txt in (
        'required',
        'together',
        'image'
    ))


def test_instance_already_created(default_args,
                                  mock_linode,
                                  capfd,
                                  access_token):
    default_args.update({
        'type': 'foo',
        'region': 'bar',
        'image': 'baz'
    })
    set_module_args(default_args)

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[mock_linode]):
        with pytest.raises(SystemExit) as sys_exit_exc:
            linode_v4.main()

    assert sys_exit_exc.value.code == 0

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['changed'] is False
    assert 'root_password' not in results['instance']
    assert (
        results['instance']['label'] ==
        mock_linode._raw_json['label']
    )


def test_instance_to_be_created_without_root_pass(default_args,
                                                  mock_linode,
                                                  capfd,
                                                  access_token):
    default_args.update({
        'type': 'foo',
        'region': 'bar',
        'image': 'baz'
    })
    set_module_args(default_args)

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[]):
        with pytest.raises(SystemExit) as sys_exit_exc:
            target = 'linode_api4.linode_client.LinodeGroup.instance_create'
            with mock.patch(target, return_value=(mock_linode, 'passw0rd')):
                linode_v4.main()

    assert sys_exit_exc.value.code == 0

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['changed'] is True
    assert (
        results['instance']['label'] ==
        mock_linode._raw_json['label']
    )
    assert results['instance']['root_pass'] == 'passw0rd'


def test_instance_to_be_created_with_root_pass(default_args,
                                               mock_linode,
                                               capfd,
                                               access_token):
    default_args.update({
        'type': 'foo',
        'region': 'bar',
        'image': 'baz',
        'root_pass': 'passw0rd',
    })
    set_module_args(default_args)

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[]):
        with pytest.raises(SystemExit) as sys_exit_exc:
            target = 'linode_api4.linode_client.LinodeGroup.instance_create'
            with mock.patch(target, return_value=mock_linode):
                linode_v4.main()

    assert sys_exit_exc.value.code == 0

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['changed'] is True
    assert (
        results['instance']['label'] ==
        mock_linode._raw_json['label']
    )
    assert 'root_pass' not in results['instance']


def test_instance_to_be_deleted(default_args,
                                mock_linode,
                                capfd,
                                access_token):
    default_args.update({'state': 'absent'})
    set_module_args(default_args)

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[mock_linode]):
        with pytest.raises(SystemExit) as sys_exit_exc:
            linode_v4.main()

    assert sys_exit_exc.value.code == 0

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['changed'] is True
    assert (
        results['instance']['label'] ==
        mock_linode._raw_json['label']
    )


def test_instance_already_deleted_no_change(default_args,
                                            mock_linode,
                                            capfd,
                                            access_token):
    default_args.update({'state': 'absent'})
    set_module_args(default_args)

    target = 'linode_api4.linode_client.LinodeGroup.instances'
    with mock.patch(target, return_value=[]):
        with pytest.raises(SystemExit) as sys_exit_exc:
            linode_v4.main()

    assert sys_exit_exc.value.code == 0

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert results['changed'] is False
    assert results['instance'] == {}


def test_user_agent_created_properly():
    try:
        from ansible.module_utils.ansible_release import (
            __version__ as ansible_version
        )
    except ImportError:
        ansible_version = 'unknown'

    expected_user_agent = 'Ansible-linode_v4_module/%s' % ansible_version
    assert expected_user_agent == get_user_agent('linode_v4_module')
