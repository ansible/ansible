import pytest

from units.compat.mock import MagicMock

from ansible.module_utils.k8s.common import K8sAnsibleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule

openshift = pytest.importorskip("openshift", minversion="0.6.2")
openshiftdynamic = openshift.dynamic

from units.modules.cloud.kubevirt.utils import (
    set_module_args,
    exit_json,
    AnsibleExitJson,
    fail_json,
    RESOURCE_DEFAULT_ARGS
)

from ansible.modules.cloud.kubevirt import kubevirt_preset as mymodule

KIND = 'VirtulMachineInstancePreset'


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
    openshiftdynamic.Resource.search = MagicMock()
    openshiftdynamic.Resource.create = MagicMock()
    openshiftdynamic.Resource.delete = MagicMock()
    # Globally mock some methods, since all tests will use this
    K8sAnsibleMixin.get_api_client = MagicMock()
    K8sAnsibleMixin.get_api_client.return_value = None
    mymodule.KubeVirtVMPreset.find_supported_resource = MagicMock()


def test_preset_creation():
    args = dict(
        state='present', name='testvmipreset',
        namespace='vms', api_version='v1',
        memory='1024Mi',
    )
    set_module_args(args)

    openshiftdynamic.Resource.get.return_value = None
    openshiftdynamic.Resource.search.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMPreset.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVMPreset().execute_module()
    assert result.value['changed']
    assert result.value['result']['method'] == 'create'


def test_preset_absent():
    args = dict(
        state='absent', name='testvmipreset',
        namespace='vms', api_version='v1',
    )
    set_module_args(args)

    openshiftdynamic.Resource.get.return_value = None
    openshiftdynamic.Resource.search.return_value = None
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMPreset.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVMPreset().execute_module()
    assert result.value['result']['method'] == 'delete'
