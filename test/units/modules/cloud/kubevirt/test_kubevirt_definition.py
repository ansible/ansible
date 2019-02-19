import pytest

from units.compat.mock import patch, MagicMock

from ansible.module_utils.k8s.common import K8sAnsibleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule

openshift = pytest.importorskip("openshift", minversion="0.6.2")
openshiftdynamic = openshift.dynamic

from units.modules.cloud.kubevirt.utils import (
    set_module_args,
    AnsibleExitJson,
    exit_json,
    AnsibleFailJson,
    fail_json,
    RESOURCE_DEFAULT_ARGS
)

from ansible.modules.clustering.k8s import k8s as mymodule


TESTABLE_KINDS = ('VirtualMachineInstance', 'VirtualMachine', 'VirtualMachineInstanceReplicaSet',
                  'VirtualMachineInstancePreset', 'PersistentVolumeClaim')


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
    # Globally mock some methods, since all tests will use this
    K8sAnsibleMixin.get_api_client = MagicMock()
    K8sAnsibleMixin.get_api_client.return_value = None
    K8sAnsibleMixin.find_resource = MagicMock()


@pytest.mark.parametrize("_phase, _exception", (('Bound', AnsibleExitJson),
                                                ('Failed', AnsibleFailJson),
                                                ('Unh4ndl3d', Exception)))
@patch('kubevirt_pvc.KubeVirtPVC._create_stream')
@pytest.mark.skip(reason='Re-enabled, when introducing k8s_pvc module')
def test_pvc_creation_wait(mock_create_stream, _phase, _exception):
    _kind = 'PersistentVolumeClaim'
    # Desired state:
    args = dict(
        state='present', kind=_kind, wait=True,
        name='testvmi', namespace='vms', api_version='v1')
    set_module_args(args)

    # Mock pre-change state:
    openshiftdynamic.Resource.get.return_value = None  # Resource does NOT initially exist in cluster
    resource_args = dict(kind=_kind, **RESOURCE_DEFAULT_ARGS)
    K8sAnsibleMixin.find_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Mock post-change state:
    stream_obj = dict(
        status=dict(phase=_phase),
        metadata=dict(annotations={'cdi.kubevirt.io/storage.pod.phase': 'Succeeded'}),
        method='create',
        changed=True,
    )
    mock_watcher = MagicMock()
    mock_create_stream.return_value = (mock_watcher, [dict(object=stream_obj)])

    # Actual test:
    with pytest.raises(_exception) as result:
        mymodule.main()
    if _exception is AnsibleExitJson:
        assert result.value[0]['method'] == 'create' and result.value[0]['changed'] is True


@pytest.mark.parametrize("_kind", TESTABLE_KINDS)
def test_resource_creation(_kind):
    # Desired state:
    args = dict(
        state='present', kind=_kind,
        name='testvmi', namespace='vms', api_version='v1')
    set_module_args(args)

    # Current state (mock):
    openshiftdynamic.Resource.get.return_value = None  # Resource does NOT exist in cluster
    resource_args = dict(kind=_kind, **RESOURCE_DEFAULT_ARGS)
    K8sAnsibleMixin.find_resource.return_value = openshiftdynamic.Resource(**resource_args)

    # Actual test:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.main()
    assert result.value['method'] == 'create' and result.value['changed'] is True
