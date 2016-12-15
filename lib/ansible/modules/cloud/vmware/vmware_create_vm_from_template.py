#!/usr/bin/python

DOCUMENTATION = '''
---
module: vmware_clone_to_folder
short_description: Clone a template or vm and place it in a given location through VMware vSphere.
description:
     - Clones a given VM or template and places it in a specified location
options:
  resource_pool:
    description:
      - The name of the resource_pool to create the VM in.
    required: false
    default: Resources
  template_location:
    description:
      - The file path to the template.
    required: True
  destination:
    description:
      - The file path to place the VM.
    required: True
extends_documentation_fragment: vmware.documentation

notes:
  - This module should run from a system that can access vSphere directly.
    Either by using local_action, or using delegate_to. This module will not
    be able to find nor place VMs or templates in the root folder.
author: "Caitlin Campbell <cacampbe@redhat.com>"
requirements:
  - "python >= 2.6"
  - pyVmomi
'''


EXAMPLES = '''
# Clone an existing template or VM into a specified folder.
- vvmware_clone_to_folder:
    hostname: vcenter.mydomain.local
    username: myuser
    password: mypass
    template_location: /templates/clienta/template436
    destination: /clients/clienta/clientaVM
'''


import ssl

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False



def connect_to_api_custom(module, disconnect_atexit=True):

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update python or or use validate_certs=false')

    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)
    except vim.fault.InvalidLogin, invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except requests.ConnectionError, connection_error:
        if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(connection_error) and not validate_certs:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)
        else:
            module.fail_json(msg="Unable to connect to vCenter or ESXi API on TCP/443.", apierror=str(connection_error))

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    return service_instance



def find_resource_pool(si, name):
    """
    Find a resource pool by it's name and return it
    """

    content = si.content
    obj_view = content.viewManager.CreateContainerView(content.rootFolder,[vim.ResourcePool],True)
    rp_list = obj_view.view

    for rp in rp_list:
        if rp.name == name:
            return rp
    return None

def vm_clone_handler(module, si, vm_name, path_list, template_vm, resource_pool_name, conn):
    """
    Will handle the thread handling to clone a virtual machine and run post processing
    """

    vm = None

    resource_pool = None
    if resource_pool_name is not None:
        resource_pool = find_resource_pool(si,resource_pool_name)
        if resource_pool is None:
            module.fail_json(msg='Unable to find resource pool %s' % resource_pool_name)


    # Find the correct folder
    folder = None

    folder = get_folder_object(conn, path_list)

    if folder is None:
        module.fail_json(msg='Unable to find %s' % str(path_list))


    relocate_spec = vim.vm.RelocateSpec(pool=resource_pool)

    clone_spec = vim.vm.CloneSpec(powerOn=False,location=relocate_spec)

    if find_by_name(folder,vm_name):
        module.exit_json(changed=False, msg='VM %s exists' % vm_name)
    else:
        task = template_vm.Clone(name=vm_name,folder=folder,spec=clone_spec)


    try:
        wait_for_task(task)
        vm = task.info.result
    except Exception, e:
        module.fail_json(msg='Unable to clone VM %s' % (vm_name),err=e.message)

    return vm


def find_by(folder, matcher_method, *args, **kwargs):
    """A generator for finding entities using a matcher_method.
    This method will search within a folder for an entity that satisfies the
    matcher_method. The matcher is called on each entity along with any
    additional arguments you pass in.
    Usage:
    ======
    code::
        for entity in folder.find_by(lambda mobj: mobj.name == 'foo'):
            print entity
            # do some work with each found entity
    code::
        def matcher(managed_object, param1, param2):
            # do stuff...
        for entity in folder.find_by(matcher, 'param1', 'param2'):
            print entity
            # do stuff...
    :type folder: vim.Folder
    :param folder: The top most folder to recursively search for the child.
    :type matcher_method: types.MethodType
    :param matcher_method: Method to call to examine the entity it must \
    return a True value on match.
    :rtype generator:
    :return: generator that produces vm.ManagedObject items.
    """
    entity_stack = folder.childEntity

    while entity_stack:
        entity = entity_stack.pop()
        if matcher_method(entity, *args, **kwargs):
            yield entity
        elif isinstance(entity, vim.Datacenter):
            # add this vim.DataCenter's folders to our search
            entity_stack.append(entity.datastoreFolder)
            entity_stack.append(entity.hostFolder)
            entity_stack.append(entity.networkFolder)
            entity_stack.append(entity.vmFolder)
        elif hasattr(entity, 'childEntity'):
            # add all child entities from this object to our search
            entity_stack.extend(entity.childEntity)


def find_by_name(folder, name):
    """Search for an entity by name.
    This method will search within the folder for an object with the name
    supplied.
    :type folder: vim.Folder
    :param folder: The top most folder to recursively search for the child.
    :type name: types.StringTypes
    :param name: Name of the child you are looking for, assumed to be unique.
    :rtype vim.ManagedEntity:
    :return: the one entity or None if no entity found.
    """
    # return only the first entity...
    for entity in find_by(folder, lambda e: e.name == name):
        return entity

def objwalk(obj, path_elements):
    if hasattr(obj, 'parent'):
        new_obj = getattr(obj, 'parent')
        if new_obj:
            if new_obj.name != 'vm':
                # 'vm' is an invisible folder that exists at the datacenter root so we ignore it
                path_elements.append(new_obj.name)

            objwalk(new_obj, path_elements)

    return path_elements


def get_folder_object(conn, path_list):

    all_vms = get_all_objs(conn, [vim.Folder])
    matching_vms = []
    name = path_list.pop()

    for vm_obj, label in all_vms.iteritems():
        if label == name:
            matching_vms.append(vm_obj)

    try:
        if len(matching_vms) > 1:

            for vm_obj in matching_vms:
                elements = []
                if set(path_list).issubset(set(objwalk(vm_obj, elements))):
                    return vm_obj

        else:
            if len(matching_vms) is 0:
                return None
            else:
                return matching_vms[0]

    except TypeError:
        module.fail_json(msg='CFolder %s notfound .' % str(path_list))

def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            template_location=dict(required=True, type='str'),
            destination=dict(required=True, type='str'),
            resource_pool=dict(required=False, default='Resources', type='str'),
            port=dict(required=False, default=443, type='int'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_PYVMOMI == False:
        module.fail_json(msg='pyvmomi is required for this module')

    hostname = module.params['hostname']

    username = module.params['username']
    password = module.params['password']
    template_location = module.params['template_location']
    destination = module.params['destination']
    resource_pool = module.params['resource_pool']
    validate_certs = module.params['validate_certs']
    port = module.params['port']

    path_list = filter(None, destination.split('/'))
    vm_name = path_list.pop(-1)

    template_path = filter(None, template_location.split('/'))
    template_name= template_path.pop(-1)

    si = connect_to_api_custom(module)
    conn = connect_to_api(module)

    template_parent_folder = get_folder_object(conn, template_path)

    if template_parent_folder is None:
        module.fail_json(msg='Could not find template in path %s.' % str(template_location))


    template = find_by_name(template_parent_folder,template_name)
    if template is None:
        module.fail_json(msg='Could not find template %s.' % str(template_name))


    finalVM = vm_clone_handler(module,si,vm_name,path_list,template,resource_pool,conn)

    if finalVM is not None:
        module.exit_json(changed=True, template_name=template_name, path=destination)
    else:
        module.fail_json(msg='Unknown error creating vm %s.' % vm_name)




# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *
if __name__ == '__main__':
    main()
