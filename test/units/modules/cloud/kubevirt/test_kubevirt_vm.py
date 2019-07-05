import pytest

openshiftdynamic = pytest.importorskip("openshift.dynamic")

from units.modules.utils import set_module_args
from units.utils.kubevirt_fixtures import base_fixture, RESOURCE_DEFAULT_ARGS, AnsibleExitJson

from ansible.module_utils.kubevirt import KubeVirtRawModule
from ansible.modules.cloud.kubevirt import kubevirt_vm as mymodule

KIND = 'VirtulMachine'


@pytest.mark.usefixtures("base_fixture")
def test_create_vm_with_multus_nowait():
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
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    openshiftdynamic.Resource.get.return_value = None  # Object doesn't exist in the cluster

    # Run code:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()

    # Verify result:
    assert result.value['changed']
    assert result.value['method'] == 'create'


@pytest.mark.usefixtures("base_fixture")
@pytest.mark.parametrize("_wait", (False, True))
def test_vm_is_absent(_wait):
    # Desired state:
    args = dict(
        state='absent', name='testvmi',
        namespace='vms',
        wait=_wait,
    )
    set_module_args(args)

    # State as "returned" by the "k8s cluster":
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    openshiftdynamic.Resource.get.return_value = None  # Object doesn't exist in the cluster

    # Run code:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()

    # Verify result:
    assert not result.value['kubevirt_vm']
    assert result.value['method'] == 'delete'
    # Note: nothing actually gets deleted, as we mock that there's not object in the cluster present,
    #       so if the method changes to something other than 'delete' at some point, that's fine


@pytest.mark.usefixtures("base_fixture")
def test_vmpreset_create():
    KIND = 'VirtulMachineInstancePreset'
    # Desired state:
    args = dict(state='present', name='testvmipreset', namespace='vms', memory='1024Mi', wait=False)
    set_module_args(args)

    # State as "returned" by the "k8s cluster":
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    openshiftdynamic.Resource.get.return_value = None  # Object doesn't exist in the cluster

    # Run code:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()

    # Verify result:
    assert result.value['changed']
    assert result.value['method'] == 'create'


@pytest.mark.usefixtures("base_fixture")
def test_vmpreset_is_absent():
    KIND = 'VirtulMachineInstancePreset'
    # Desired state:
    args = dict(state='absent', name='testvmipreset', namespace='vms')
    set_module_args(args)

    # State as "returned" by the "k8s cluster":
    resource_args = dict(kind=KIND, **RESOURCE_DEFAULT_ARGS)
    KubeVirtRawModule.find_supported_resource.return_value = openshiftdynamic.Resource(**resource_args)
    openshiftdynamic.Resource.get.return_value = None  # Object doesn't exist in the cluster

    # Run code:
    with pytest.raises(AnsibleExitJson) as result:
        mymodule.KubeVirtVM().execute_module()

    # Verify result:
    assert not result.value['kubevirt_vm']
    assert result.value['method'] == 'delete'
    # Note: nothing actually gets deleted, as we mock that there's not object in the cluster present,
    #       so if the method changes to something other than 'delete' at some point, that's fine
