import json
import pytest

from units.compat.mock import patch, MagicMock

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.k8s.common import K8sAnsibleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule
from ansible.module_utils.kubevirt import KubeVirtRawModule

from ansible.modules.cloud.kubevirt import kubevirt_vm as mymodule

openshiftdynamic = pytest.importorskip("openshift.dynamic")
helpexceptions = pytest.importorskip("openshift.helper.exceptions")

KIND = 'VirtulMachine'
RESOURCE_DEFAULT_ARGS = {'api_version': 'v1alpha3', 'group': 'kubevirt.io',
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
def setup_mixtures(monkeypatch):
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
    KubeVirtRawModule.find_supported_resource = MagicMock()


def test_vm_multus_creation():
    # Desired state:
    args = dict(
        state='present', name='testvm',
        namespace='vms',
        interfaces=[
            {'bridge': {}, 'name': 'default', 'network': {'pod': {}}},
            {'bridge': {}, 'name': 'mynet', 'network': {'multus': {'networkName': 'mynet'}}},
        ],
        wait=False,
    )
    set_module_args(args)

    # State as "returned" by the "k8s cluster":
    openshiftdynamic.Resource.get.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()
    assert result.value['changed']
    assert result.value['method'] == 'create'


@pytest.mark.parametrize("_wait", (False, True))
def test_resource_absent(_wait):
    # Desired state:
    args = dict(
        state='absent', name='testvmi',
        namespace='vms',
        wait=_wait,
    )
    set_module_args(args)

    # State as "returned" by the "k8s cluster":
    openshiftdynamic.Resource.get.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()
    assert result.value['method'] == 'delete'
    assert not result.value['kubevirt_vm']
