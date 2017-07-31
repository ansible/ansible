#!/usr/bin/python
#
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure
short_description: create or terminate a virtual machine in azure
description:
     - Creates or terminates azure instances. When created optionally waits for it to be 'running'.
version_added: "1.7"
options:
  name:
    description:
      - name of the virtual machine and associated cloud service.
    required: true
    default: null
  location:
    description:
      - the azure location to use (e.g. 'East US')
    required: true
    default: null
  subscription_id:
    description:
      - azure subscription id. Overrides the AZURE_SUBSCRIPTION_ID environment variable.
    required: false
    default: null
  management_cert_path:
    description:
      - path to an azure management certificate associated with the subscription id. Overrides the AZURE_CERT_PATH environment variable.
    required: false
    default: null
  storage_account:
    description:
      - the azure storage account in which to store the data disks.
    required: true
  image:
    description:
      - system image for creating the virtual machine
        (e.g., b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu_DAILY_BUILD-precise-12_04_3-LTS-amd64-server-20131205-en-us-30GB)
    required: true
    default: null
  role_size:
    description:
      - azure role size for the new virtual machine (e.g., Small, ExtraLarge, A6). You have to pay attention to the fact that instances of
        type G and DS are not available in all regions (locations). Make sure if you selected the size and type of instance available in your chosen location.
    required: false
    default: Small
  endpoints:
    description:
      - a comma-separated list of TCP ports to expose on the virtual machine (e.g., "22,80")
    required: false
    default: 22
  user:
    description:
      - the unix username for the new virtual machine.
    required: false
    default: null
  password:
    description:
      - the unix password for the new virtual machine.
    required: false
    default: null
  ssh_cert_path:
    description:
      - path to an X509 certificate containing the public ssh key to install in the virtual machine.
        See http://www.windowsazure.com/en-us/manage/linux/tutorials/intro-to-linux/ for more details.
      - if this option is specified, password-based ssh authentication will be disabled.
    required: false
    default: null
  virtual_network_name:
    description:
      - Name of virtual network.
    required: false
    default: null
  hostname:
    description:
      - hostname to write /etc/hostname. Defaults to <name>.cloudapp.net.
    required: false
    default: null
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
    aliases: []
  wait_timeout_redirects:
    description:
      - how long before wait gives up for redirects, in seconds
    default: 300
    aliases: []
  state:
    description:
      - create or terminate instances
    required: false
    default: 'present'
    aliases: []
  auto_updates:
    description:
      - Enable Auto Updates on Windows Machines
    required: false
    version_added: "2.0"
    default: "no"
    choices: [ "yes", "no" ]
  enable_winrm:
    description:
      - Enable winrm on Windows Machines
    required: false
    version_added: "2.0"
    default: "yes"
    choices: [ "yes", "no" ]
  os_type:
    description:
      - The type of the os that is gettings provisioned
    required: false
    version_added: "2.0"
    default: "linux"
    choices: [ "windows", "linux" ]

requirements:
    - "python >= 2.6"
    - "azure >= 0.7.1"
author: "John Whitbeck (@jwhitbeck)"
'''

EXAMPLES = '''
# Note: None of these examples set subscription_id or management_cert_path
# It is assumed that their matching environment variables are set.

- name: Provision virtual machine example
  azure:
    name: my-virtual-machine
    role_size: Small
    image: b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu_DAILY_BUILD-precise-12_04_3-LTS-amd64-server-20131205-en-us-30GB
    location: East US
    user: ubuntu
    ssh_cert_path: /path/to/azure_x509_cert.pem
    storage_account: my-storage-account
    wait: True
    state: present
  delegate_to: localhost

- name: Terminate virtual machine example
  azure:
    name: my-virtual-machine
    state: absent
  delegate_to: localhost

- name: Create windows machine
  azure:
    name: ben-Winows-23
    hostname: win123
    os_type: windows
    enable_winrm: True
    subscription_id: '{{ azure_sub_id }}'
    management_cert_path: '{{ azure_cert_path }}'
    role_size: Small
    image: bd507d3a70934695bc2128e3e5a255ba__RightImage-Windows-2012-x64-v13.5
    location: East Asia
    password: xxx
    storage_account: benooytes
    user: admin
    wait: True
    state: present
    virtual_network_name: '{{ vnet_name }}'
  delegate_to: localhost
'''

import base64
import datetime
import os
import signal
import time
from urlparse import urlparse
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.timeout import TimeoutError

AZURE_LOCATIONS = ['South Central US',
                   'Central US',
                   'East US 2',
                   'East US',
                   'West US',
                   'North Central US',
                   'North Europe',
                   'West Europe',
                   'East Asia',
                   'Southeast Asia',
                   'Japan West',
                   'Japan East',
                   'Brazil South']

AZURE_ROLE_SIZES = ['ExtraSmall',
                    'Small',
                    'Medium',
                    'Large',
                    'ExtraLarge',
                    'A5',
                    'A6',
                    'A7',
                    'A8',
                    'A9',
                    'Basic_A0',
                    'Basic_A1',
                    'Basic_A2',
                    'Basic_A3',
                    'Basic_A4',
                    'Standard_D1',
                    'Standard_D2',
                    'Standard_D3',
                    'Standard_D4',
                    'Standard_D11',
                    'Standard_D12',
                    'Standard_D13',
                    'Standard_D14',
                    'Standard_D1_v2',
                    'Standard_D2_v2',
                    'Standard_D3_v2',
                    'Standard_D4_v2',
                    'Standard_D5_v2',
                    'Standard_D11_v2',
                    'Standard_D12_v2',
                    'Standard_D13_v2',
                    'Standard_D14_v2',
                    'Standard_DS1',
                    'Standard_DS2',
                    'Standard_DS3',
                    'Standard_DS4',
                    'Standard_DS11',
                    'Standard_DS12',
                    'Standard_DS13',
                    'Standard_DS14',
                    'Standard_G1',
                    'Standard_G2',
                    'Standard_G3',
                    'Standard_G4',
                    'Standard_G5']

from distutils.version import LooseVersion

try:
    import azure as windows_azure

    if hasattr(windows_azure, '__version__') and LooseVersion(windows_azure.__version__) <= "0.11.1":
        from azure import WindowsAzureError as AzureException
        from azure import WindowsAzureMissingResourceError as AzureMissingException
    else:
        from azure.common import AzureException as AzureException
        from azure.common import AzureMissingResourceHttpError as AzureMissingException

    from azure.servicemanagement import (ServiceManagementService, OSVirtualHardDisk, SSH, PublicKeys,
                                         PublicKey, LinuxConfigurationSet, ConfigurationSetInputEndpoints,
                                         ConfigurationSetInputEndpoint, Listener, WindowsConfigurationSet)

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

from types import MethodType
import json


def _wait_for_completion(azure, promise, wait_timeout, msg):
    if not promise:
        return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        operation_result = azure.get_operation_status(promise.request_id)
        time.sleep(5)
        if operation_result.status == "Succeeded":
            return

    raise AzureException('Timed out waiting for async operation ' + msg + ' "' + str(promise.request_id) + '" to complete.')


def _delete_disks_when_detached(azure, wait_timeout, disk_names):
    def _handle_timeout(signum, frame):
        raise TimeoutError("Timeout reached while waiting for disks to become detached.")

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(wait_timeout)
    try:
        while len(disk_names) > 0:
            for disk_name in disk_names:
                disk = azure.get_disk(disk_name)
                if disk.attached_to is None:
                    azure.delete_disk(disk.name, True)
                    disk_names.remove(disk_name)
    except AzureException as e:
        raise AzureException("failed to get or delete disk %s, error was: %s" % (disk_name, str(e)))
    finally:
        signal.alarm(0)


def get_ssh_certificate_tokens(module, ssh_cert_path):
    """
    Returns the sha1 fingerprint and a base64-encoded PKCS12 version of the certificate.
    """
    # This returns a string such as SHA1 Fingerprint=88:60:0B:13:A9:14:47:DA:4E:19:10:7D:34:92:2B:DF:A1:7D:CA:FF
    rc, stdout, stderr = module.run_command(['openssl', 'x509', '-in', ssh_cert_path, '-fingerprint', '-noout'])
    if rc != 0:
        module.fail_json(msg="failed to generate the key fingerprint, error was: %s" % stderr)
    fingerprint = stdout.strip()[17:].replace(':', '')

    rc, stdout, stderr = module.run_command(['openssl', 'pkcs12', '-export', '-in', ssh_cert_path, '-nokeys', '-password', 'pass:'])
    if rc != 0:
        module.fail_json(msg="failed to generate the pkcs12 signature from the certificate, error was: %s" % stderr)
    pkcs12_base64 = base64.b64encode(stdout.strip())

    return (fingerprint, pkcs12_base64)


def create_virtual_machine(module, azure):
    """
    Create new virtual machine

    module : AnsibleModule object
    azure: authenticated azure ServiceManagementService object

    Returns:
        True if a new virtual machine and/or cloud service was created, false otherwise
    """
    name = module.params.get('name')
    os_type = module.params.get('os_type')
    hostname = module.params.get('hostname') or name + ".cloudapp.net"
    endpoints = module.params.get('endpoints').split(',')
    ssh_cert_path = module.params.get('ssh_cert_path')
    user = module.params.get('user')
    password = module.params.get('password')
    location = module.params.get('location')
    role_size = module.params.get('role_size')
    storage_account = module.params.get('storage_account')
    image = module.params.get('image')
    virtual_network_name = module.params.get('virtual_network_name')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    changed = False

    # Check if a deployment with the same name already exists
    cloud_service_name_available = azure.check_hosted_service_name_availability(name)
    if cloud_service_name_available.result:
        # cloud service does not exist; create it
        try:
            result = azure.create_hosted_service(service_name=name, label=name, location=location)
            _wait_for_completion(azure, result, wait_timeout, "create_hosted_service")
            changed = True
        except AzureException as e:
            module.fail_json(msg="failed to create the new service, error was: %s" % str(e))

    try:
        # check to see if a vm with this name exists; if so, do nothing
        azure.get_role(name, name, name)
    except AzureMissingException:
        # vm does not exist; create it

        if os_type == 'linux':
            # Create linux configuration
            disable_ssh_password_authentication = not password
            vm_config = LinuxConfigurationSet(hostname, user, password, disable_ssh_password_authentication)
        else:
            # Create Windows Config
            vm_config = WindowsConfigurationSet(hostname, password, None, module.params.get('auto_updates'), None, user)
            vm_config.domain_join = None
            if module.params.get('enable_winrm'):
                listener = Listener('Http')
                vm_config.win_rm.listeners.listeners.append(listener)
            else:
                vm_config.win_rm = None

        # Add ssh certificates if specified
        if ssh_cert_path:
            fingerprint, pkcs12_base64 = get_ssh_certificate_tokens(module, ssh_cert_path)
            # Add certificate to cloud service
            result = azure.add_service_certificate(name, pkcs12_base64, 'pfx', '')
            _wait_for_completion(azure, result, wait_timeout, "add_service_certificate")

            # Create ssh config
            ssh_config = SSH()
            ssh_config.public_keys = PublicKeys()
            authorized_keys_path = u'/home/%s/.ssh/authorized_keys' % user
            ssh_config.public_keys.public_keys.append(PublicKey(path=authorized_keys_path, fingerprint=fingerprint))
            # Append ssh config to linux machine config
            vm_config.ssh = ssh_config

        # Create network configuration
        network_config = ConfigurationSetInputEndpoints()
        network_config.configuration_set_type = 'NetworkConfiguration'
        network_config.subnet_names = []
        network_config.public_ips = None
        for port in endpoints:
            network_config.input_endpoints.append(ConfigurationSetInputEndpoint(name='TCP-%s' % port,
                                                                                protocol='TCP',
                                                                                port=port,
                                                                                local_port=port))

        # First determine where to store disk
        today = datetime.date.today().strftime('%Y-%m-%d')
        disk_prefix = u'%s-%s' % (name, name)
        media_link = u'http://%s.blob.core.windows.net/vhds/%s-%s.vhd' % (storage_account, disk_prefix, today)
        # Create system hard disk
        os_hd = OSVirtualHardDisk(image, media_link)

        # Spin up virtual machine
        try:
            result = azure.create_virtual_machine_deployment(service_name=name,
                                                             deployment_name=name,
                                                             deployment_slot='production',
                                                             label=name,
                                                             role_name=name,
                                                             system_config=vm_config,
                                                             network_config=network_config,
                                                             os_virtual_hard_disk=os_hd,
                                                             role_size=role_size,
                                                             role_type='PersistentVMRole',
                                                             virtual_network_name=virtual_network_name)
            _wait_for_completion(azure, result, wait_timeout, "create_virtual_machine_deployment")
            changed = True
        except AzureException as e:
            module.fail_json(msg="failed to create the new virtual machine, error was: %s" % str(e))

    try:
        deployment = azure.get_deployment_by_name(service_name=name, deployment_name=name)
        return (changed, urlparse(deployment.url).hostname, deployment)
    except AzureException as e:
        module.fail_json(msg="failed to lookup the deployment information for %s, error was: %s" % (name, str(e)))


def terminate_virtual_machine(module, azure):
    """
    Terminates a virtual machine

    module : AnsibleModule object
    azure: authenticated azure ServiceManagementService object

    Returns:
        True if a new virtual machine was deleted, false otherwise
    """

    # Whether to wait for termination to complete before returning
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    name = module.params.get('name')
    delete_empty_services = module.params.get('delete_empty_services')

    changed = False

    deployment = None
    public_dns_name = None
    disk_names = []
    try:
        deployment = azure.get_deployment_by_name(service_name=name, deployment_name=name)
    except AzureMissingException as e:
        pass  # no such deployment or service
    except AzureException as e:
        module.fail_json(msg="failed to find the deployment, error was: %s" % str(e))

    # Delete deployment
    if deployment:
        changed = True
        try:
            # gather disk info
            results = []
            for role in deployment.role_list:
                role_props = azure.get_role(name, deployment.name, role.role_name)
                if role_props.os_virtual_hard_disk.disk_name not in disk_names:
                    disk_names.append(role_props.os_virtual_hard_disk.disk_name)
        except AzureException as e:
            module.fail_json(msg="failed to get the role %s, error was: %s" % (role.role_name, str(e)))

        try:
            result = azure.delete_deployment(name, deployment.name)
            _wait_for_completion(azure, result, wait_timeout, "delete_deployment")
        except AzureException as e:
            module.fail_json(msg="failed to delete the deployment %s, error was: %s" % (deployment.name, str(e)))

        # It's unclear when disks associated with terminated deployment get detached.
        # Thus, until the wait_timeout is reached, we continue to delete disks as they
        # become detached by polling the list of remaining disks and examining the state.
        try:
            _delete_disks_when_detached(azure, wait_timeout, disk_names)
        except (AzureException, TimeoutError) as e:
            module.fail_json(msg=str(e))

        try:
            # Now that the vm is deleted, remove the cloud service
            result = azure.delete_hosted_service(service_name=name)
            _wait_for_completion(azure, result, wait_timeout, "delete_hosted_service")
        except AzureException as e:
            module.fail_json(msg="failed to delete the service %s, error was: %s" % (name, str(e)))
        public_dns_name = urlparse(deployment.url).hostname

    return changed, public_dns_name, deployment


def get_azure_creds(module):
    # Check module args for credentials, then check environment vars
    subscription_id = module.params.get('subscription_id')
    if not subscription_id:
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', None)
    if not subscription_id:
        module.fail_json(msg="No subscription_id provided. Please set 'AZURE_SUBSCRIPTION_ID' or use the 'subscription_id' parameter")

    management_cert_path = module.params.get('management_cert_path')
    if not management_cert_path:
        management_cert_path = os.environ.get('AZURE_CERT_PATH', None)
    if not management_cert_path:
        module.fail_json(msg="No management_cert_path provided. Please set 'AZURE_CERT_PATH' or use the 'management_cert_path' parameter")

    return subscription_id, management_cert_path


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ssh_cert_path=dict(),
            name=dict(),
            hostname=dict(),
            os_type=dict(default='linux', choices=['linux', 'windows']),
            location=dict(choices=AZURE_LOCATIONS),
            role_size=dict(choices=AZURE_ROLE_SIZES),
            subscription_id=dict(no_log=True),
            storage_account=dict(),
            management_cert_path=dict(),
            endpoints=dict(default='22'),
            user=dict(),
            password=dict(no_log=True),
            image=dict(),
            virtual_network_name=dict(default=None),
            state=dict(default='present'),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(default=600),
            wait_timeout_redirects=dict(default=300),
            auto_updates=dict(type='bool', default=False),
            enable_winrm=dict(type='bool', default=True),
        )
    )
    if not HAS_AZURE:
        module.fail_json(msg='azure python module required for this module')
    # create azure ServiceManagementService object
    subscription_id, management_cert_path = get_azure_creds(module)

    wait_timeout_redirects = int(module.params.get('wait_timeout_redirects'))

    if hasattr(windows_azure, '__version__') and LooseVersion(windows_azure.__version__) <= "0.8.0":
        # wrapper for handling redirects which the sdk <= 0.8.0 is not following
        azure = Wrapper(ServiceManagementService(subscription_id, management_cert_path), wait_timeout_redirects)
    else:
        azure = ServiceManagementService(subscription_id, management_cert_path)

    cloud_service_raw = None
    if module.params.get('state') == 'absent':
        (changed, public_dns_name, deployment) = terminate_virtual_machine(module, azure)

    elif module.params.get('state') == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new instance')
        if not module.params.get('image'):
            module.fail_json(msg='image parameter is required for new instance')
        if not module.params.get('user'):
            module.fail_json(msg='user parameter is required for new instance')
        if not module.params.get('location'):
            module.fail_json(msg='location parameter is required for new instance')
        if not module.params.get('storage_account'):
            module.fail_json(msg='storage_account parameter is required for new instance')
        if not (module.params.get('password') or module.params.get('ssh_cert_path')):
            module.fail_json(msg='password or ssh_cert_path parameter is required for new instance')
        (changed, public_dns_name, deployment) = create_virtual_machine(module, azure)

    module.exit_json(changed=changed, public_dns_name=public_dns_name, deployment=json.loads(json.dumps(deployment, default=lambda o: o.__dict__)))


class Wrapper(object):
    def __init__(self, obj, wait_timeout):
        self.other = obj
        self.wait_timeout = wait_timeout

    def __getattr__(self, name):
        if hasattr(self.other, name):
            func = getattr(self.other, name)
            return lambda *args, **kwargs: self._wrap(func, args, kwargs)
        raise AttributeError(name)

    def _wrap(self, func, args, kwargs):
        if isinstance(func, MethodType):
            result = self._handle_temporary_redirects(lambda: func(*args, **kwargs))
        else:
            result = self._handle_temporary_redirects(lambda: func(self.other, *args, **kwargs))
        return result

    def _handle_temporary_redirects(self, f):
        wait_timeout = time.time() + self.wait_timeout
        while wait_timeout > time.time():
            try:
                return f()
            except AzureException as e:
                if not str(e).lower().find("temporary redirect") == -1:
                    time.sleep(5)
                    pass
                else:
                    raise e


if __name__ == '__main__':
    main()
