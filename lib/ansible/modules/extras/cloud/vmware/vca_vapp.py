#!/usr/bin/python

# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



DOCUMENTATION = '''
---
module: vca_vapp
short_description: create, terminate, start or stop a vm in vca
description:
  - Creates or terminates vca vms.
version_added: "2.0"
options:
    username:
      description:
        - The vca username or email address, if not set the environment variable VCA_USER is checked for the username.
      required: false
      default: None
    password:
      description:
        - The vca password, if not set the environment variable VCA_PASS is checked for the password
      required: false
      default: None
    org:
      description:
        - The org to login to for creating vapp, mostly set when the service_type is vdc.
      required: false
      default: None
    service_id:
      description:
        - The service id in a vchs environment to be used for creating the vapp
      required: false
      default: None
    host:
      description:
        - The authentication host to be used when service type  is vcd.
      required: false
      default: None
    api_version:
      description:
        - The api version to be used with the vca
      required: false
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against
      required: false
      default: vca
      choices: [ "vca", "vchs", "vcd" ]
    state:
      description:
        - if the object should be added or removed
      required: false
      default: present
      choices: [ "present", "absent" ]
    catalog_name:
      description:
        - The catalog from which the vm template is used.
      required: false
      default: "Public Catalog"
    script:
      description:
        - The path to script that gets injected to vm during creation.
      required: false
      default: "Public Catalog"
    template_name:
      description:
        - The template name from which the vm should be created.
      required: True
    network_name:
      description:
        - The network name to which the vm should be attached.
      required: false
      default: 'None'
    network_ip:
      description:
        - The ip address that should be assigned to vm when the ip assignment type is static
      required: false
      default: None
    network_mode:
      description:
        - The network mode in which the ip should be allocated.
      required: false
      default: pool
      choices: [ "pool", "dhcp", 'static' ]
    instance_id::
      description:
        - The instance id of the region in vca flavour where the vm should be created
      required: false
      default: None
    wait:
      description:
        - If the module should wait if the operation is poweroff or poweron, is better to wait to report the right state. 
      required: false
      default: True
    wait_timeout:
      description:
        - The wait timeout when wait is set to true
      required: false
      default: 250
    vdc_name:
      description:
        - The name of the vdc where the vm should be created.
      required: false
      default: None
    vm_name:
      description:
        - The name of the vm to be created, the vapp is named the same as the vapp name
      required: false
      default: 'default_ansible_vm1'
    vm_cpus:
      description:
        - The number if cpus to be added to the vm
      required: false
      default: None
    vm_memory:
      description:
        - The amount of memory to be added to vm in megabytes
      required: false
      default: None
    verify_certs:
      description:
        - If the certificates of the authentication is to be verified
      required: false
      default: True
    admin_password:
      description:
        - The password to be set for admin
      required: false
      default: None
    operation:
      description:
        - The operation to be done on the vm
      required: false
      default: poweroff
      choices: [ 'shutdown', 'poweroff', 'poweron', 'reboot', 'reset', 'suspend' ]

'''

EXAMPLES = '''

#Create a vm in an vca environment. The username password is not set as they are set in environment

- hosts: localhost
  connection: local
  tasks:
   - vca_vapp:
       operation: poweroff
       instance_id: 'b15ff1e5-1024-4f55-889f-ea0209726282'
       vdc_name: 'benz_ansible'
       vm_name: benz
       vm_cpus: 2
       vm_memory: 1024
       network_mode: pool
       template_name: "CentOS63-32BIT"
       admin_password: "Password!123"
       network_name: "default-routed-network"

#Create a vm in a vchs environment.

- hosts: localhost
  connection: local
  tasks:
   - vca_app:
       operation: poweron
       service_id: '9-69'
       vdc_name: 'Marketing'
       service_type: 'vchs'
       vm_name: benz
       vm_cpus: 1
       script: "/tmp/configure_vm.sh"
       catalog_name: "Marketing-Catalog"
       template_name: "Marketing-Ubuntu-1204x64"
       vm_memory: 512
       network_name: "M49-default-isolated"

#create a vm in a vdc environment

- hosts: localhost
  connection: local
  tasks:
   - vca_vapp:
       operation: poweron
       org: IT20
       host: "mycloud.vmware.net"
       api_version: "5.5"
       service_type: vcd
       vdc_name: 'IT20 Data Center (Beta)'
       vm_name: benz
       vm_cpus: 1
       catalog_name: "OS Templates"
       template_name: "CentOS 6.5 64Bit CLI"
       network_mode: pool


'''


import time, json, xmltodict

HAS_PYVCLOUD = False
try:
    from pyvcloud.vcloudair import VCA
    HAS_PYVCLOUD = True
except ImportError:
        pass

SERVICE_MAP         = {'vca': 'ondemand', 'vchs': 'subscription', 'vcd': 'vcd'}
LOGIN_HOST          = {}
LOGIN_HOST['vca']   = 'vca.vmware.com'
LOGIN_HOST['vchs']  = 'vchs.vmware.com'
VM_COMPARE_KEYS     = ['admin_password', 'status', 'cpus', 'memory_mb']

def vm_state(val=None):
    if  val == 8:
        return "Power_Off"
    elif val == 4:
        return "Power_On"
    else:
        return "Unknown Status"

def serialize_instances(instance_list):
    instances = []
    for i in instance_list:
        instances.append(dict(apiUrl=i['apiUrl'], instance_id=i['id']))
    return instances

def get_catalogs(vca):
    catalogs = vca.get_catalogs()
    results = []
    for catalog in catalogs:
        if catalog.CatalogItems and catalog.CatalogItems.CatalogItem:
            for item in catalog.CatalogItems.CatalogItem:
                results.append([catalog.name, item.name])
        else:
            results.append([catalog.name, ''])
    return results

def vca_login(module=None):
    service_type    = module.params.get('service_type')
    username        = module.params.get('username')
    password        = module.params.get('password')
    instance        = module.params.get('instance_id')
    org             = module.params.get('org')
    service         = module.params.get('service_id')
    vdc_name        = module.params.get('vdc_name')
    version         = module.params.get('api_version')
    verify          = module.params.get('verify_certs')
    if not vdc_name:
        if service_type == 'vchs':
            vdc_name = module.params.get('service_id')
    if not org:
        if service_type == 'vchs':
            if vdc_name:
                org = vdc_name
            else:
                org = service
    if service_type == 'vcd':
        host = module.params.get('host')
    else:
        host = LOGIN_HOST[service_type]

    if not username:
        if 'VCA_USER' in os.environ:
            username = os.environ['VCA_USER']
    if not password:
        if 'VCA_PASS' in os.environ:
            password = os.environ['VCA_PASS']
    if not username or not password:
        module.fail_json(msg = "Either the username or password is not set, please check")

    if service_type == 'vchs':
        version = '5.6'
    if service_type == 'vcd':
        if not version:
            version == '5.6'


    vca = VCA(host=host, username=username, service_type=SERVICE_MAP[service_type], version=version, verify=verify)

    if service_type == 'vca':
        if not vca.login(password=password):
            module.fail_json(msg = "Login Failed: Please check username or password", error=vca.response.content)
        if not vca.login_to_instance(password=password, instance=instance, token=None, org_url=None):
            s_json = serialize_instances(vca.instances)
            module.fail_json(msg = "Login to Instance failed: Seems like instance_id provided is wrong .. Please check",\
                                    valid_instances=s_json)
        if not vca.login_to_instance(instance=instance, password=None, token=vca.vcloud_session.token,
                                     org_url=vca.vcloud_session.org_url):
            module.fail_json(msg = "Error logging into org for the instance", error=vca.response.content)
        return vca

    if service_type == 'vchs':
        if not vca.login(password=password):
            module.fail_json(msg = "Login Failed: Please check username or password", error=vca.response.content)
        if not vca.login(token=vca.token):
            module.fail_json(msg = "Failed to get the token", error=vca.response.content)
        if not vca.login_to_org(service, org):
            module.fail_json(msg = "Failed to login to org, Please check the orgname", error=vca.response.content)
        return vca

    if service_type == 'vcd':
        if not vca.login(password=password, org=org):
            module.fail_json(msg = "Login Failed: Please check username or password or host parameters")
        if not vca.login(password=password, org=org):
            module.fail_json(msg = "Failed to get the token", error=vca.response.content)
        if not vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url):
            module.fail_json(msg = "Failed to login to org", error=vca.response.content)
        return vca
  
def set_vm_state(module=None, vca=None, state=None):
        wait          = module.params.get('wait')
        wait_tmout    = module.params.get('wait_timeout')
        vm_name       = module.params.get('vm_name')
        vdc_name      = module.params.get('vdc_name')
        vapp_name     = module.params.get('vm_name')
        service_type    = module.params.get('service_type') 
        service_id    = module.params.get('service_id') 
        if service_type == 'vchs' and not vdc_name:
            vdc_name = service_id
        vdc = vca.get_vdc(vdc_name)
        if wait:
            tmout = time.time() + wait_tmout
            while tmout > time.time():
                vapp = vca.get_vapp(vdc, vapp_name)
                vms = filter(lambda vm: vm['name'] == vm_name, vapp.get_vms_details())
                vm = vms[0]
                if vm['status'] == state:
                    return True
                time.sleep(5)
            module.fail_json(msg="Timeut waiting for the vms state to change")
        return True

def vm_details(vdc=None, vapp=None, vca=None):
    table = []
    networks = []
    vm_name = vapp
    vdc1 = vca.get_vdc(vdc)
    if not vdc1:
        module.fail_json(msg = "Error getting the vdc, Please check the vdc name")
    vap = vca.get_vapp(vdc1, vapp)
    if vap:
        vms = filter(lambda vm: vm['name'] == vm_name, vap.get_vms_details())
    networks = vap.get_vms_network_info()
    if len(networks[0]) >= 1:
        table.append(dict(vm_info=vms[0], network_info=networks[0][0]))
    else:
        table.append(dict(vm_info=vms[0], network_info=networks[0]))
    return table


def vapp_attach_net(module=None, vca=None, vapp=None):
    network_name        = module.params.get('network_name')
    service_type        = module.params.get('service_type')
    vdc_name            = module.params.get('vdc_name')
    mode                = module.params.get('network_mode')
    if mode.upper() == 'STATIC': 
        network_ip  = module.params.get('network_ip')
    else:
        network_ip = None
    if not vdc_name:
        if service_type == 'vchs':
            vdc_name = module.params.get('service_id')
    nets = filter(lambda n: n.name == network_name, vca.get_networks(vdc_name))
    if len(nets) <= 1:
        net_task = vapp.disconnect_vms()
        if not net_task:
            module.fail_json(msg="Failure in detattaching vms from vnetworks", error=vapp.response.content)
        if not vca.block_until_completed(net_task):
            module.fail_json(msg="Failure in waiting for detaching vms from vnetworks", error=vapp.response.content)
        net_task = vapp.disconnect_from_networks()
        if not net_task:
            module.fail_json(msg="Failure in detattaching network from vapp", error=vapp.response.content)
        if not vca.block_until_completed(net_task):
            module.fail_json(msg="Failure in waiting for detaching network from vapp", error=vapp.response.content)
        if not network_name:
            return True
        
        net_task = vapp.connect_to_network(nets[0].name, nets[0].href)
        if not net_task:
            module.fail_json(msg="Failure in attaching network to vapp", error=vapp.response.content)
        if not vca.block_until_completed(net_task):
            module.fail_json(msg="Failure in waiting for attching network to vapp", error=vapp.response.content)
        
        net_task = vapp.connect_vms(nets[0].name, connection_index=0, ip_allocation_mode=mode.upper(), ip_address=network_ip )
        if not net_task:
            module.fail_json(msg="Failure in attaching network to vm", error=vapp.response.content)
        if not vca.block_until_completed(net_task):
            module.fail_json(msg="Failure in waiting for attaching network to vm", error=vapp.response.content)
        return True
    nets = []
    for i in vca.get_networks(vdc_name):
        nets.append(i.name)
    module.fail_json(msg="Seems like network_name is not found in the vdc, please check Available networks as above", Available_networks=nets)

def create_vm(vca=None, module=None):
    vm_name        = module.params.get('vm_name')
    operation      = module.params.get('operation')
    vm_cpus        = module.params.get('vm_cpus')
    vm_memory      = module.params.get('vm_memory')
    catalog_name   = module.params.get('catalog_name')
    template_name  = module.params.get('template_name')
    vdc_name       = module.params.get('vdc_name')
    network_name   = module.params.get('network_name')
    service_type   = module.params.get('service_type')
    admin_pass     = module.params.get('admin_password')
    script         = module.params.get('script')
    vapp_name      = vm_name

    if not vdc_name:
        if service_type == 'vchs':
            vdc_name = module.params.get('service_id')
    task = vca.create_vapp(vdc_name, vapp_name, template_name, catalog_name, vm_name=None)
    if not task:
        catalogs = get_catalogs(vca) 
        module.fail_json(msg="Error in Creating VM, Please check catalog or template, Available catalogs and templates are as above or check the error field", catalogs=catalogs, errors=vca.response.content)
    if not vca.block_until_completed(task):
        module.fail_json(msg = "Error in waiting for VM Creation, Please check logs", errors=vca.response.content)
    vdc = vca.get_vdc(vdc_name)
    if not vdc:
        module.fail_json(msg = "Error getting the vdc, Please check the vdc name", errors=vca.response.content)
    
    vapp = vca.get_vapp(vdc, vapp_name)
    task = vapp.modify_vm_name(1, vm_name)
    if not task:
        module.fail_json(msg="Error in setting the vm_name to vapp_name",  errors=vca.response.content)
    if not vca.block_until_completed(task):
        module.fail_json(msg = "Error in waiting for VM Renaming, Please check logs", errors=vca.response.content)
    vapp = vca.get_vapp(vdc, vapp_name)
    task = vapp.customize_guest_os(vm_name, computer_name=vm_name)
    if not task:
        module.fail_json(msg="Error in setting the computer_name to vm_name",  errors=vca.response.content)
    if not vca.block_until_completed(task):
        module.fail_json(msg = "Error in waiting for Computer Renaming, Please check logs", errors=vca.response.content)

    
    if network_name:
        vapp = vca.get_vapp(vdc, vapp_name)
        if not vapp_attach_net(module, vca, vapp):
            module.fail_json(msg= "Attaching network to VM fails", errors=vca.response.content)

    if vm_cpus:
        vapp = vca.get_vapp(vdc, vapp_name)
        task = vapp.modify_vm_cpu(vm_name, vm_cpus)
        if not task:
            module.fail_json(msg="Error adding cpu", error=vapp.resonse.contents)
        if not vca.block_until_completed(task):
            module.fail_json(msg="Failure in waiting for modifying cpu", error=vapp.response.content)

    if vm_memory:
        vapp = vca.get_vapp(vdc, vapp_name)
        task = vapp.modify_vm_memory(vm_name, vm_memory)
        if not task:
            module.fail_json(msg="Error adding memory", error=vapp.resonse.contents)
        if not vca.block_until_completed(task):
            module.fail_json(msg="Failure in waiting for modifying memory", error=vapp.response.content)
 
    if admin_pass:
        vapp = vca.get_vapp(vdc, vapp_name)
        task = vapp.customize_guest_os(vm_name, customization_script=None,
                                           computer_name=None, admin_password=admin_pass,
                                                                      reset_password_required=False)
        if not task:
            module.fail_json(msg="Error adding admin password", error=vapp.resonse.contents)
        if not vca.block_until_completed(task):
            module.fail_json(msg = "Error in waiting for resettng admin pass, Please check logs", errors=vapp.response.content)
    
    if script:
        vapp = vca.get_vapp(vdc, vapp_name)
        if os.path.exists(os.path.expanduser(script)):
            file_contents = open(script, 'r')
            task = vapp.customize_guest_os(vm_name, customization_script=file_contents.read())
            if not task:
                module.fail_json(msg="Error adding customization script", error=vapp.resonse.contents)
            if not vca.block_until_completed(task):
                module.fail_json(msg = "Error in waiting for customization script, please check logs", errors=vapp.response.content)
            task = vapp.force_customization(vm_name, power_on=False )
            if not task:
                module.fail_json(msg="Error adding customization script", error=vapp.resonse.contents)
            if not vca.block_until_completed(task):
                module.fail_json(msg = "Error in waiting for customization script, please check logs", errors=vapp.response.content)
        else:
            module.fail_json(msg = "The file specified in script paramter is not avaialable or accessible")
            
    vapp = vca.get_vapp(vdc, vapp_name)
    if operation == 'poweron':  
        vapp.poweron()
        set_vm_state(module, vca, state='Powered on')
    elif operation == 'poweroff':
        vapp.poweroff()
    elif operation == 'reboot':
        vapp.reboot()
    elif operation == 'reset':
        vapp.reset()
    elif operation == 'suspend':
        vapp.suspend()
    elif operation == 'shutdown':
        vapp.shutdown()
    details = vm_details(vdc_name, vapp_name, vca)
    module.exit_json(changed=True, msg="VM created", vm_details=details[0])

def vapp_reconfigure(module=None, diff=None, vm=None, vca=None, vapp=None, vdc_name=None):
    flag        = False
    vapp_name   = module.params.get('vm_name') 
    vm_name     = module.params.get('vm_name') 
    cpus        = module.params.get('vm_cpus') 
    memory      = module.params.get('vm_memory') 
    admin_pass  = module.params.get('admin_password') 

    if 'status' in diff:
        operation = module.params.get('operation')
        if operation == 'poweroff':
            vapp.poweroff()
            set_vm_state(module, vca, state='Powered off')
        flag = True
    if 'network' in diff:
        vapp_attach_net(module, vca, vapp)
        flag = True
    if 'cpus' in diff:
        task = vapp.modify_vm_cpu(vm_name, cpus)
        if not vca.block_until_completed(task):
            module.fail_json(msg="Failure in waiting for modifying cpu, might be vm is powered on and doesnt support hotplugging", error=vapp.response.content)
        flag = True
    if 'memory_mb' in diff:
        task = vapp.modify_vm_memory(vm_name, memory)
        if not vca.block_until_completed(task):
            module.fail_json(msg="Failure in waiting for modifying memory, might be vm is powered on and doesnt support hotplugging", error=vapp.response.content)
        flag = True
    if 'admin_password' in diff:
        task = vapp.customize_guest_os(vm_name, customization_script=None,
                                           computer_name=None, admin_password=admin_pass,
                                                                      reset_password_required=False)
        if not task:
            module.fail_json(msg="Error adding admin password", error=vapp.resonse.contents)
        if not vca.block_until_completed(task):
            module.fail_json(msg = "Error in waiting for resettng admin pass, Please check logs", errors=vapp.response.content)
        flag = True
    if 'status' in diff:
        operation = module.params.get('operation')
        if operation == 'poweron':
            vapp.poweron()
            set_vm_state(module, vca, state='Powered on')
        elif operation == 'reboot':
            vapp.reboot()
        elif operation == 'reset':
            vapp.reset()
        elif operation == 'suspend':
            vapp.suspend()
        elif operation == 'shutdown':
            vapp.shutdown()
        flag = True
    details = vm_details(vdc_name, vapp_name, vca)
    if flag:
        module.exit_json(changed=True, msg="VM reconfigured", vm_details=details[0])
    module.exit_json(changed=False, msg="VM exists as per configuration",\
                     vm_details=details[0])

def vm_exists(module=None, vapp=None, vca=None, vdc_name=None):
    vm_name       = module.params.get('vm_name')
    operation     = module.params.get('operation')
    vm_cpus       = module.params.get('vm_cpus')
    vm_memory     = module.params.get('vm_memory')
    network_name  = module.params.get('network_name')
    admin_pass    = module.params.get('admin_password')

    d_vm = {}
    d_vm['name']           = vm_name
    d_vm['cpus']           = vm_cpus
    d_vm['memory_mb']      = vm_memory
    d_vm['admin_password'] = admin_pass

    if operation == 'poweron':
        d_vm['status'] = 'Powered on'
    elif operation == 'poweroff':
        d_vm['status'] = 'Powered off'
    else:
        d_vm['status'] = 'operate'

    vms = filter(lambda vm: vm['name'] == vm_name, vapp.get_vms_details())
    if len(vms) > 1:
        module.fail_json(msg = "The vapp seems to have more than one vm with same name,\
                                currently we only support a single vm deployment")
    elif len(vms) == 0:
        return False 

    else:
        vm = vms[0]
        diff = []
        for i in VM_COMPARE_KEYS:
            if not d_vm[i]:
                continue
            if vm[i] != d_vm[i]:
                diff.append(i)
        if len(diff) == 1 and 'status' in diff:
            vapp_reconfigure(module, diff, vm, vca, vapp, vdc_name)
        networks = vapp.get_vms_network_info()
        if not network_name and len(networks) >=1:
            if len(networks[0]) >= 1:
                if networks[0][0]['network_name'] != 'none': 
                    diff.append('network')
        if not network_name:
            if len(diff) == 0:
                return True
        if not networks[0] and network_name:
            diff.append('network')
        if networks[0]:
            if len(networks[0]) >= 1:
                if networks[0][0]['network_name'] != network_name:
                    diff.append('network')
        if vm['status'] != 'Powered off':
            if operation != 'poweroff' and len(diff) > 0:
                module.fail_json(msg="To change any properties of a vm, The vm should be in Powered Off state")
        if len(diff) == 0:
            return True
        else:
            vapp_reconfigure(module, diff, vm, vca, vapp, vdc_name)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            username            = dict(default=None),
            password            = dict(default=None),
            org                 = dict(default=None),
            service_id          = dict(default=None),
            script              = dict(default=None),
            host                = dict(default=None),
            api_version         = dict(default='5.7'),
            service_type        = dict(default='vca', choices=['vchs', 'vca', 'vcd']),
            state               = dict(default='present', choices = ['present', 'absent']),
            catalog_name        = dict(default="Public Catalog"),
            template_name       = dict(default=None, required=True),
            network_name        = dict(default=None),
            network_ip          = dict(default=None),
            network_mode        = dict(default='pool', choices=['dhcp', 'static', 'pool']),
            instance_id         = dict(default=None),
            wait                = dict(default=True, type='bool'),
            wait_timeout        = dict(default=250, type='int'),
            vdc_name            = dict(default=None),
            vm_name             = dict(default='default_ansible_vm1'),
            vm_cpus             = dict(default=None, type='int'),
            verify_certs        = dict(default=True, type='bool'),
            vm_memory           = dict(default=None, type='int'),
            admin_password      = dict(default=None),
            operation           = dict(default='poweroff', choices=['shutdown', 'poweroff', 'poweron', 'reboot', 'reset', 'suspend'])
        )
    )


    vdc_name        = module.params.get('vdc_name')
    vm_name         = module.params.get('vm_name')
    org             = module.params.get('org')
    service         = module.params.get('service_id')
    state           = module.params.get('state')
    service_type    = module.params.get('service_type')
    host            = module.params.get('host')
    instance_id     = module.params.get('instance_id')
    network_mode    = module.params.get('network_mode')
    network_ip      = module.params.get('network_ip')
    vapp_name       = vm_name

    if not HAS_PYVCLOUD:
        module.fail_json(msg="python module pyvcloud is needed for this module")

    if network_mode.upper() == 'STATIC':
        if not network_ip:
            module.fail_json(msg="if network_mode is STATIC, network_ip is mandatory")

    if service_type == 'vca':
        if not instance_id:
            module.fail_json(msg="When service type is vca the instance_id parameter is mandatory")
        if not vdc_name:
            module.fail_json(msg="When service type is vca the vdc_name parameter is mandatory")

    if service_type == 'vchs':
        if not service:
            module.fail_json(msg="When service type vchs the service_id parameter is mandatory")
        if not org:
            org = service
        if not vdc_name:
            vdc_name = service
    if service_type == 'vcd':
        if not host:
            module.fail_json(msg="When service type is vcd host parameter is mandatory")
    
    vca = vca_login(module)
    vdc = vca.get_vdc(vdc_name)
    if not vdc:
        module.fail_json(msg = "Error getting the vdc, Please check the vdc name")
    vapp = vca.get_vapp(vdc, vapp_name)
    if vapp:
        if state == 'absent':
            task = vca.delete_vapp(vdc_name, vapp_name)
            if not vca.block_until_completed(task):
                module.fail_json(msg="failure in deleting vapp")
            module.exit_json(changed=True, msg="Vapp deleted")
        if vm_exists(module, vapp, vca, vdc_name ):
            details = vm_details(vdc_name, vapp_name, vca)
            module.exit_json(changed=False, msg="vapp exists", vm_details=details[0])
        else:
            create_vm(vca, module)
    if state == 'absent':
        module.exit_json(changed=False, msg="Vapp does not exist")
    create_vm(vca, module)
        

    
# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
        main()
