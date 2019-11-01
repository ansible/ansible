import pytest

openshiftdynamic = pytest.importorskip("openshift.dynamic")

from units.modules.utils import set_module_args
from units.utils.kubevirt_fixtures import base_fixture, RESOURCE_DEFAULT_ARGS, AnsibleExitJson

from ansible.module_utils.k8s.raw import KubernetesRawModule
from ansible.modules.cloud.kubevirt import kubevirt_rs as mymodule

KIND = 'VirtualMachineInstanceReplicaSet'


@pytest.mark.usefixtures("base_fixture")
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
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMIRS.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    res_inst = openshiftdynamic.ResourceInstance('', dict(kind=KIND, metadata={'name': _name}, spec={'replicas': 2}))
    openshiftdynamic.Resource.get.return_value = res_inst
    openshiftdynamic.Resource.search.return_value = [res_inst]

    # Final state, after patching the object
    KubernetesRawModule.patch_resource.return_value = dict(kind=KIND, metadata={'name': _name},
                                                           spec={'replicas': _replicas}), None

    # Run code:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVMIRS().execute_module()

    # Verify result:
    assert result.value['changed'] == _changed


@pytest.mark.usefixtures("base_fixture")
@pytest.mark.parametrize("_replicas, _success", ((1, False),
                                                 (2, False),
                                                 (5, True),))
def test_scale_rs_wait(_replicas, _success):
    _name = 'test-rs'
    # Desired state:
    args = dict(name=_name, namespace='vms', replicas=5, wait=True)
    set_module_args(args)

    # Mock pre-change state:
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    mymodule.KubeVirtVMIRS.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    res_inst = openshiftdynamic.ResourceInstance('', dict(kind=KIND, metadata={'name': _name}, spec={'replicas': 2}))
    openshiftdynamic.Resource.get.return_value = res_inst
    openshiftdynamic.Resource.search.return_value = [res_inst]

    # ~Final state, after patching the object (`replicas` match desired state)
    KubernetesRawModule.patch_resource.return_value = dict(kind=KIND, name=_name, metadata={'name': _name},
                                                           spec={'replicas': 5}), None

    # Final final state, as returned by resource.watch()
    final_obj = dict(metadata=dict(name=_name), status=dict(readyReplicas=_replicas), **resource_args)
    event = openshiftdynamic.ResourceInstance(None, final_obj)
    openshiftdynamic.Resource.watch.return_value = [dict(object=event)]

    # Run code:
    with pytest.raises(Exception) as result:
        mymodule.KubeVirtVMIRS().execute_module()

    # Verify result:
    assert result.value['success'] == _success
