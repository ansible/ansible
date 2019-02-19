import pytest

from units.compat.mock import patch, MagicMock

from ansible.module_utils.k8s.common import K8sAnsibleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule

openshift = pytest.importorskip("openshift", minversion="0.6.2")
openshiftdynamic = openshift.dynamic
helpexceptions = pytest.importorskip("openshift.helper.exceptions", minversion="0.6.2")

from units.modules.cloud.kubevirt.utils import (
    set_module_args,
    AnsibleExitJson,
    exit_json,
    AnsibleFailJson,
    fail_json,
    RESOURCE_DEFAULT_ARGS
)

from ansible.modules.cloud.kubevirt import kubevirt_rs as mymodule


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
    # Globally mock some methods, since all tests will use this
    KubernetesRawModule.patch_resource = MagicMock()
    KubernetesRawModule.patch_resource.return_value = ({}, None)
    K8sAnsibleMixin.get_api_client = MagicMock()
    K8sAnsibleMixin.get_api_client.return_value = None
    mymodule.KubeVirtVMIRS.find_supported_resource = MagicMock()


@pytest.mark.parametrize("_replicas, _changed", ((1, True),
                                                 (3, True),
                                                 (2, False),
                                                 (5, True),))
def test_scale_rs_nowait(_replicas, _changed):
    _name = 'test-rs'
    # Desired state:
    args = dict(name=_name, namespace='vms', replicas=_replicas, wait=False)
    set_module_args(args)

    # Mock pre-change state:
    resource_args = dict(kind='VirtualMachineInstanceReplicaSet', **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMIRS.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    res_inst = openshiftdynamic.ResourceInstance('', dict(metadata={'name': _name}, spec={'replicas': 2}))
    openshiftdynamic.Resource.get.return_value = res_inst
    openshiftdynamic.Resource.search.return_value = [res_inst]
    KubernetesRawModule.patch_resource.return_value = dict(metadata={'name': _name}, spec={'replicas': _replicas}), None

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVMIRS().execute_module()
    assert result.value['changed'] == _changed


@pytest.mark.parametrize("_replicas, _changed", ((1, True),
                                                 (2, False),
                                                 (5, True),))
@patch('kubevirt_rs.KubeVirtVMIRS._create_stream')
def test_scale_rs_wait(mock_create_stream, _replicas, _changed):
    _name = 'test-rs'
    # Desired state:
    args = dict(name=_name, namespace='vms', replicas=_replicas, wait=True)
    set_module_args(args)

    # Mock pre-change state:
    resource_args = dict(kind='VirtualMachineInstanceReplicaSet', **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMIRS.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    res_inst = openshiftdynamic.ResourceInstance('', dict(metadata={'name': _name}, spec={'replicas': 2}))
    openshiftdynamic.Resource.get.return_value = res_inst
    openshiftdynamic.Resource.search.return_value = [res_inst]
    KubernetesRawModule.patch_resource.return_value = dict(metadata={'name': _name}, spec={'replicas': _replicas}), None

    # Mock post-change state:
    stream_obj = dict(
        status=dict(readyReplicas=_replicas),
        metadata=dict(name=_name)
    )
    mock_watcher = MagicMock()
    mock_create_stream.return_value = (mock_watcher, [dict(object=stream_obj)])

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVMIRS().execute_module()
    assert result.value['changed'] == _changed


@patch('openshift.watch.Watch')
def test_stream_creation(mock_watch):
    _name = 'test-rs'
    # Desired state:
    args = dict(name=_name, namespace='vms', replicas=2, wait=True)
    set_module_args(args)

    # Mock pre-change state:
    resource_args = dict(kind='VirtualMachineInstanceReplicaSet', **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMIRS.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    res_inst = openshiftdynamic.ResourceInstance('', dict(metadata={'name': _name}, spec={'replicas': 3}))
    openshiftdynamic.Resource.get.return_value = res_inst
    openshiftdynamic.Resource.search.return_value = [res_inst]

    # Actual test:
    mock_watch.side_effect = helpexceptions.KubernetesException("Test", value=42)
    with pytest.raises(AnsibleFailJson):
        mymodule.KubeVirtVMIRS().execute_module()
