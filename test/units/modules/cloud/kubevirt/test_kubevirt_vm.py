import json
import pytest

from units.compat.mock import patch, MagicMock

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.k8s.common import K8sAnsibleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule

from ansible.modules.cloud.kubevirt import kubevirt_vm as mymodule

openshiftdynamic = pytest.importorskip("openshift.dynamic", minversion="0.6.2")
helpexceptions = pytest.importorskip("openshift.helper.exceptions", minversion="0.6.2")

KIND = 'VirtulMachine'
RESOURCE_DEFAULT_ARGS = {'api_version': 'v1', 'group': 'kubevirt.io',
                         'prefix': 'apis', 'namespaced': True}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught
    by the test case"""
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __getitem__(self, attr):
        return getattr(self, attr)


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught
    by the test case"""
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __getitem__(self, attr):
        return getattr(self, attr)


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(**kwargs)


def fail_json(*args, **kwargs):
    raise AnsibleFailJson(**kwargs)


@pytest.fixture(autouse=True)
def setup_mixtures(self, monkeypatch):
    monkeypatch.setattr(
        KubernetesRawModule, "exit_json", exit_json)
    monkeypatch.setattr(
        KubernetesRawModule, "fail_json", fail_json)
    # Create mock methods in Resource directly, otherwise dyn client
    # tries binding those to corresponding methods in DynamicClient
    # (with partial()), which is more problematic to intercept
    openshiftdynamic.Resource.get = MagicMock()
    openshiftdynamic.Resource.create = MagicMock()
    openshiftdynamic.Resource.delete = MagicMock()
    openshiftdynamic.Resource.patch = MagicMock()
    # Globally mock some methods, since all tests will use this
    K8sAnsibleMixin.get_api_client = MagicMock()
    K8sAnsibleMixin.get_api_client.return_value = None
    K8sAnsibleMixin.find_resource = MagicMock()


def test_vm_multus_creation(self):
    args = dict(
        state='present', name='testvm',
        namespace='vms', api_version='v1',
        interfaces=[
            {'bridge': {}, 'name': 'default', 'network': {'pod': {}}},
            {'bridge': {}, 'name': 'mynet', 'network': {'multus': {'networkName': 'mynet'}}},
        ],
        wait=False,
    )
    set_module_args(args)

    openshiftdynamic.Resource.get.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    K8sAnsibleMixin.find_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()
    assert result.value['changed']
    assert result.value['result']['method'] == 'create'


@pytest.mark.parametrize("_wait", (False, True))
def test_resource_absent(self, _wait):
    # Desired state:
    args = dict(
        state='absent', name='testvmi',
        namespace='vms', api_version='v1',
        wait=_wait,
    )
    set_module_args(args)

    openshiftdynamic.Resource.get.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    K8sAnsibleMixin.find_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()
    assert result.value['result']['method'] == 'delete'


@patch('openshift.watch.Watch')
def test_stream_creation(self, mock_watch):
    # Desired state:
    args = dict(
        state='running', name='testvmi', namespace='vms',
        api_version='v1', wait=True,
    )
    set_module_args(args)

    # Actual test:
    mock_watch.side_effect = helpexceptions.KubernetesException("Test", value=42)
    with pytest.raises(AnsibleFailJson):
        mymodule.KubeVirtVM().execute_module()


def test_simple_merge_dicts(self):
    dict1 = {'labels': {'label1': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtVM.merge_dicts(dict1, dict2)), sort_keys=True)


def test_simple_multi_merge_dicts(self):
    dict1 = {'labels': {'label1': 'value', 'label3': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtVM.merge_dicts(dict1, dict2)), sort_keys=True)


def test_double_nested_merge_dicts(self):
    dict1 = {'metadata': {'labels': {'label1': 'value', 'label3': 'value'}}}
    dict2 = {'metadata': {'labels': {'label2': 'value'}}}
    dict3 = json.dumps({'metadata': {'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtVM.merge_dicts(dict1, dict2)), sort_keys=True)
