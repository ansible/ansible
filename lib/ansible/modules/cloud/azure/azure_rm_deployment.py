#!/usr/bin/python
#
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_deployment

short_description: Create or destroy Azure Resource Manager template deployments

version_added: "2.1"

description:
     - "Create or destroy Azure Resource Manager template deployments via the Azure SDK for Python.
       You can find some quick start templates in GitHub here https://github.com/azure/azure-quickstart-templates.
       For more information on Azue resource manager templates see https://azure.microsoft.com/en-us/documentation/articles/resource-group-template-deploy/."

options:
  resource_group_name:
    description:
      - The resource group name to use or create to host the deployed template
    required: true
    aliases:
      - resource_group
  location:
    description:
      - The geo-locations in which the resource group will be located.
    default: westus
  deployment_mode:
    description:
      - In incremental mode, resources are deployed without deleting existing resources that are not included in the template.
        In complete mode resources are deployed and existing resources in the resource group not included in the template are deleted.
    default: incremental
    choices:
        - complete
        - incremental
  state:
    description:
      - If state is "present", template will be created. If state is "present" and if deployment exists, it will be
        updated. If state is "absent", stack will be removed.
    default: present
    choices:
        - present
        - absent
  template:
    description:
      - A hash containing the templates inline. This parameter is mutually exclusive with 'template_link'.
        Either one of them is required if "state" parameter is "present".
    type: dict
  template_link:
    description:
      - Uri of file containing the template body. This parameter is mutually exclusive with 'template'. Either one
        of them is required if "state" parameter is "present".
  parameters:
    description:
      - A hash of all the required template variables for the deployment template. This parameter is mutually exclusive
        with 'parameters_link'. Either one of them is required if "state" parameter is "present".
    type: dict
  parameters_link:
    description:
      - Uri of file containing the parameters body. This parameter is mutually exclusive with 'parameters'. Either
        one of them is required if "state" parameter is "present".
  deployment_name:
    description:
      - The name of the deployment to be tracked in the resource group deployment history. Re-using a deployment name
        will overwrite the previous value in the resource group's deployment history.
    default: ansible-arm
  wait_for_deployment_completion:
    description:
      - Whether or not to block until the deployment has completed.
    type: bool
    default: 'yes'
  wait_for_deployment_polling_period:
    description:
      - Time (in seconds) to wait between polls when waiting for deployment completion.
    default: 10

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - David Justice (@devigned)
    - Laurent Mazuel (@lmazuel)
    - Andre Price (@obsoleted)

'''

EXAMPLES = '''
# Destroy a template deployment
- name: Destroy Azure Deploy
  azure_rm_deployment:
    state: absent
    subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    resource_group_name: dev-ops-cle

# Create or update a template deployment based on uris using parameter and template links
- name: Create Azure Deploy
  azure_rm_deployment:
    state: present
    resource_group_name: dev-ops-cle
    template_link: 'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.json'
    parameters_link: 'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-simple-linux/azuredeploy.parameters.json'

# Create or update a template deployment based on a uri to the template and parameters specified inline.
# This deploys a VM with SSH support for a given public key, then stores the result in 'azure_vms'. The result is then
# used to create a new host group. This host group is then used to wait for each instance to respond to the public IP SSH.
---
- hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: Destroy Azure Deploy
      azure_rm_deployment:
        state: absent
        subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        resource_group_name: dev-ops-cle

    - name: Create Azure Deploy
      azure_rm_deployment:
        state: present
        subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        resource_group_name: dev-ops-cle
        parameters:
          newStorageAccountName:
            value: devopsclestorage1
          adminUsername:
            value: devopscle
          dnsNameForPublicIP:
            value: devopscleazure
          location:
            value: West US
          vmSize:
            value: Standard_A2
          vmName:
            value: ansibleSshVm
          sshKeyData:
            value: YOUR_SSH_PUBLIC_KEY
        template_link: 'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-vm-sshkey/azuredeploy.json'
      register: azure

    - name: Add new instance to host group
      add_host:
        hostname: "{{ item['ips'][0].public_ip }}"
        groupname: azure_vms
      with_items: "{{ azure.deployment.instances }}"

    - hosts: azure_vms
      user: devopscle
      tasks:
        - name: Wait for SSH to come up
          wait_for:
            port: 22
            timeout: 2000
            state: started
        - name: echo the hostname of the vm
          shell: hostname

# Deploy an Azure WebApp running a hello world'ish node app
- name: Create Azure WebApp Deployment at http://devopscleweb.azurewebsites.net/hello.js
  azure_rm_deployment:
    state: present
    subscription_id: cbbdaed0-fea9-4693-bf0c-d446ac93c030
    resource_group_name: dev-ops-cle-webapp
    parameters:
      repoURL:
        value: 'https://github.com/devigned/az-roadshow-oss.git'
      siteName:
        value: devopscleweb
      hostingPlanName:
        value: someplan
      siteLocation:
        value: westus
      sku:
        value: Standard
    template_link: 'https://raw.githubusercontent.com/azure/azure-quickstart-templates/master/201-web-app-github-deploy/azuredeploy.json'

# Create or update a template deployment based on an inline template and parameters
- name: Create Azure Deploy
  azure_rm_deployment:
    state: present
    subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    resource_group_name: dev-ops-cle

    template:
      $schema: "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
      contentVersion: "1.0.0.0"
      parameters:
        newStorageAccountName:
          type: "string"
          metadata:
            description: "Unique DNS Name for the Storage Account where the Virtual Machine's disks will be placed."
        adminUsername:
          type: "string"
          metadata:
            description: "User name for the Virtual Machine."
        adminPassword:
          type: "securestring"
          metadata:
            description: "Password for the Virtual Machine."
        dnsNameForPublicIP:
          type: "string"
          metadata:
            description: "Unique DNS Name for the Public IP used to access the Virtual Machine."
        ubuntuOSVersion:
          type: "string"
          defaultValue: "14.04.2-LTS"
          allowedValues:
            - "12.04.5-LTS"
            - "14.04.2-LTS"
            - "15.04"
          metadata:
            description: >
                         The Ubuntu version for the VM. This will pick a fully patched image of this given Ubuntu version.
                         Allowed values: 12.04.5-LTS, 14.04.2-LTS, 15.04."
      variables:
        location: "West US"
        imagePublisher: "Canonical"
        imageOffer: "UbuntuServer"
        OSDiskName: "osdiskforlinuxsimple"
        nicName: "myVMNic"
        addressPrefix: "192.0.2.0/24"
        subnetName: "Subnet"
        subnetPrefix: "10.0.0.0/24"
        storageAccountType: "Standard_LRS"
        publicIPAddressName: "myPublicIP"
        publicIPAddressType: "Dynamic"
        vmStorageAccountContainerName: "vhds"
        vmName: "MyUbuntuVM"
        vmSize: "Standard_D1"
        virtualNetworkName: "MyVNET"
        vnetID: "[resourceId('Microsoft.Network/virtualNetworks',variables('virtualNetworkName'))]"
        subnetRef: "[concat(variables('vnetID'),'/subnets/',variables('subnetName'))]"
      resources:
        - type: "Microsoft.Storage/storageAccounts"
          name: "[parameters('newStorageAccountName')]"
          apiVersion: "2015-05-01-preview"
          location: "[variables('location')]"
          properties:
            accountType: "[variables('storageAccountType')]"
        - apiVersion: "2015-05-01-preview"
          type: "Microsoft.Network/publicIPAddresses"
          name: "[variables('publicIPAddressName')]"
          location: "[variables('location')]"
          properties:
            publicIPAllocationMethod: "[variables('publicIPAddressType')]"
            dnsSettings:
              domainNameLabel: "[parameters('dnsNameForPublicIP')]"
        - type: "Microsoft.Network/virtualNetworks"
          apiVersion: "2015-05-01-preview"
          name: "[variables('virtualNetworkName')]"
          location: "[variables('location')]"
          properties:
            addressSpace:
              addressPrefixes:
                - "[variables('addressPrefix')]"
            subnets:
              -
                name: "[variables('subnetName')]"
                properties:
                  addressPrefix: "[variables('subnetPrefix')]"
        - type: "Microsoft.Network/networkInterfaces"
          apiVersion: "2015-05-01-preview"
          name: "[variables('nicName')]"
          location: "[variables('location')]"
          dependsOn:
            - "[concat('Microsoft.Network/publicIPAddresses/', variables('publicIPAddressName'))]"
            - "[concat('Microsoft.Network/virtualNetworks/', variables('virtualNetworkName'))]"
          properties:
            ipConfigurations:
              -
                name: "ipconfig1"
                properties:
                  privateIPAllocationMethod: "Dynamic"
                  publicIPAddress:
                    id: "[resourceId('Microsoft.Network/publicIPAddresses',variables('publicIPAddressName'))]"
                  subnet:
                    id: "[variables('subnetRef')]"
        - type: "Microsoft.Compute/virtualMachines"
          apiVersion: "2015-06-15"
          name: "[variables('vmName')]"
          location: "[variables('location')]"
          dependsOn:
            - "[concat('Microsoft.Storage/storageAccounts/', parameters('newStorageAccountName'))]"
            - "[concat('Microsoft.Network/networkInterfaces/', variables('nicName'))]"
          properties:
            hardwareProfile:
              vmSize: "[variables('vmSize')]"
            osProfile:
              computername: "[variables('vmName')]"
              adminUsername: "[parameters('adminUsername')]"
              adminPassword: "[parameters('adminPassword')]"
            storageProfile:
              imageReference:
                publisher: "[variables('imagePublisher')]"
                offer: "[variables('imageOffer')]"
                sku: "[parameters('ubuntuOSVersion')]"
                version: "latest"
              osDisk:
                name: "osdisk"
                vhd:
                  uri: >
                       [concat('http://',parameters('newStorageAccountName'),'.blob.core.windows.net/',variables('vmStorageAccountContainerName'),'/',
                       variables('OSDiskName'),'.vhd')]
                caching: "ReadWrite"
                createOption: "FromImage"
            networkProfile:
              networkInterfaces:
                -
                  id: "[resourceId('Microsoft.Network/networkInterfaces',variables('nicName'))]"
            diagnosticsProfile:
              bootDiagnostics:
                enabled: "true"
                storageUri: "[concat('http://',parameters('newStorageAccountName'),'.blob.core.windows.net')]"
    parameters:
      newStorageAccountName:
        value: devopsclestorage
      adminUsername:
        value: devopscle
      adminPassword:
        value: Password1!
      dnsNameForPublicIP:
        value: devopscleazure
'''

RETURN = '''
deployment:
  description: Deployment details
  type: dict
  returned: always
  sample:
      group_name:
        description: Name of the resource group
        type: string
        returned: always
      id:
        description: The Azure ID of the deployment
        type: string
        returned: always
      instances:
        description: Provides the public IP addresses for each VM instance.
        type: list
        returned: always
      name:
        description: Name of the deployment
        type: string
        returned: always
      outputs:
        description: Dictionary of outputs received from the deployment
        type: dict
        returned: always
'''

import time

try:
    from azure.common.credentials import ServicePrincipalCredentials
    import time
    import yaml
except ImportError as exc:
    IMPORT_ERROR = "Error importing module prerequisites: %s" % exc

try:
    from itertools import chain
    from azure.common.exceptions import CloudError
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.network import NetworkManagementClient

except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


class AzureRMDeploymentManager(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group_name=dict(type='str', required=True, aliases=['resource_group']),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            template=dict(type='dict', default=None),
            parameters=dict(type='dict', default=None),
            template_link=dict(type='str', default=None),
            parameters_link=dict(type='str', default=None),
            location=dict(type='str', default="westus"),
            deployment_mode=dict(type='str', default='incremental', choices=['complete', 'incremental']),
            deployment_name=dict(type='str', default="ansible-arm"),
            wait_for_deployment_completion=dict(type='bool', default=True),
            wait_for_deployment_polling_period=dict(type='int', default=10)
        )

        mutually_exclusive = [('template', 'template_link'),
                              ('parameters', 'parameters_link')]

        self.resource_group_name = None
        self.state = None
        self.template = None
        self.parameters = None
        self.template_link = None
        self.parameters_link = None
        self.location = None
        self.deployment_mode = None
        self.deployment_name = None
        self.wait_for_deployment_completion = None
        self.wait_for_deployment_polling_period = None
        self.tags = None
        self.append_tags = None

        self.results = dict(
            deployment=dict(),
            changed=False,
            msg=""
        )

        super(AzureRMDeploymentManager, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       mutually_exclusive=mutually_exclusive,
                                                       supports_check_mode=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['append_tags', 'tags']:
            setattr(self, key, kwargs[key])

        if self.state == 'present':
            deployment = self.deploy_template()
            if deployment is None:
                self.results['deployment'] = dict(
                    name=self.deployment_name,
                    group_name=self.resource_group_name,
                    id=None,
                    outputs=None,
                    instances=None
                )
            else:
                self.results['deployment'] = dict(
                    name=deployment.name,
                    group_name=self.resource_group_name,
                    id=deployment.id,
                    outputs=deployment.properties.outputs,
                    instances=self._get_instances(deployment)
                )

            self.results['changed'] = True
            self.results['msg'] = 'deployment succeeded'
        else:
            try:
                if self.get_resource_group(self.resource_group_name):
                    self.destroy_resource_group()
                    self.results['changed'] = True
                    self.results['msg'] = "deployment deleted"
            except CloudError:
                # resource group does not exist
                pass

        return self.results

    def deploy_template(self):
        """
        Deploy the targeted template and parameters
        :param module: Ansible module containing the validated configuration for the deployment template
        :param client: resource management client for azure
        :param conn_info: connection info needed
        :return:
        """

        deploy_parameter = self.rm_models.DeploymentProperties(self.deployment_mode)
        if not self.parameters_link:
            deploy_parameter.parameters = self.parameters
        else:
            deploy_parameter.parameters_link = self.rm_models.ParametersLink(
                uri=self.parameters_link
            )
        if not self.template_link:
            deploy_parameter.template = self.template
        else:
            deploy_parameter.template_link = self.rm_models.TemplateLink(
                uri=self.template_link
            )

        if self.append_tags and self.tags:
            try:
                # fetch the RG directly (instead of using the base helper) since we don't want to exit if it's missing
                rg = self.rm_client.resource_groups.get(self.resource_group_name)
                if rg.tags:
                    self.tags = dict(self.tags, **rg.tags)
            except CloudError:
                # resource group does not exist
                pass

        params = self.rm_models.ResourceGroup(location=self.location, tags=self.tags)

        try:
            self.rm_client.resource_groups.create_or_update(self.resource_group_name, params)
        except CloudError as exc:
            self.fail("Resource group create_or_update failed with status code: %s and message: %s" %
                      (exc.status_code, exc.message))
        try:
            result = self.rm_client.deployments.create_or_update(self.resource_group_name,
                                                                 self.deployment_name,
                                                                 deploy_parameter)

            deployment_result = None
            if self.wait_for_deployment_completion:
                deployment_result = self.get_poller_result(result)
                while deployment_result.properties is None or deployment_result.properties.provisioning_state not in ['Canceled', 'Failed', 'Deleted',
                                                                                                                      'Succeeded']:
                    time.sleep(self.wait_for_deployment_polling_period)
                    deployment_result = self.rm_client.deployments.get(self.resource_group_name, self.deployment_name)
        except CloudError as exc:
            failed_deployment_operations = self._get_failed_deployment_operations(self.deployment_name)
            self.log("Deployment failed %s: %s" % (exc.status_code, exc.message))
            self.fail("Deployment failed with status code: %s and message: %s" % (exc.status_code, exc.message),
                      failed_deployment_operations=failed_deployment_operations)

        if self.wait_for_deployment_completion and deployment_result.properties.provisioning_state != 'Succeeded':
            self.log("provisioning state: %s" % deployment_result.properties.provisioning_state)
            failed_deployment_operations = self._get_failed_deployment_operations(self.deployment_name)
            self.fail('Deployment failed. Deployment id: %s' % deployment_result.id,
                      failed_deployment_operations=failed_deployment_operations)

        return deployment_result

    def destroy_resource_group(self):
        """
        Destroy the targeted resource group
        """
        try:
            result = self.rm_client.resource_groups.delete(self.resource_group_name)
            result.wait()  # Blocking wait till the delete is finished
        except CloudError as e:
            if e.status_code == 404 or e.status_code == 204:
                return
            else:
                self.fail("Delete resource group and deploy failed with status code: %s and message: %s" %
                          (e.status_code, e.message))

    def _get_failed_nested_operations(self, current_operations):
        new_operations = []
        for operation in current_operations:
            if operation.properties.provisioning_state == 'Failed':
                new_operations.append(operation)
                if operation.properties.target_resource and \
                   'Microsoft.Resources/deployments' in operation.properties.target_resource.id:
                    nested_deployment = operation.properties.target_resource.resource_name
                    try:
                        nested_operations = self.rm_client.deployment_operations.list(self.resource_group_name,
                                                                                      nested_deployment)
                    except CloudError as exc:
                        self.fail("List nested deployment operations failed with status code: %s and message: %s" %
                                  (exc.status_code, exc.message))
                    new_nested_operations = self._get_failed_nested_operations(nested_operations)
                    new_operations += new_nested_operations
        return new_operations

    def _get_failed_deployment_operations(self, deployment_name):
        results = []
        # time.sleep(15) # there is a race condition between when we ask for deployment status and when the
        #               # status is available.

        try:
            operations = self.rm_client.deployment_operations.list(self.resource_group_name, deployment_name)
        except CloudError as exc:
            self.fail("Get deployment failed with status code: %s and message: %s" %
                      (exc.status_code, exc.message))
        try:
            results = [
                dict(
                    id=op.id,
                    operation_id=op.operation_id,
                    status_code=op.properties.status_code,
                    status_message=op.properties.status_message,
                    target_resource=dict(
                        id=op.properties.target_resource.id,
                        resource_name=op.properties.target_resource.resource_name,
                        resource_type=op.properties.target_resource.resource_type
                    ) if op.properties.target_resource else None,
                    provisioning_state=op.properties.provisioning_state,
                )
                for op in self._get_failed_nested_operations(operations)
            ]
        except:
            # If we fail here, the original error gets lost and user receives wrong error message/stacktrace
            pass
        self.log(dict(failed_deployment_operations=results), pretty_print=True)
        return results

    def _get_instances(self, deployment):
        dep_tree = self._build_hierarchy(deployment.properties.dependencies)
        vms = self._get_dependencies(dep_tree, resource_type="Microsoft.Compute/virtualMachines")
        vms_and_nics = [(vm, self._get_dependencies(vm['children'], "Microsoft.Network/networkInterfaces"))
                        for vm in vms]
        vms_and_ips = [(vm['dep'], self._nic_to_public_ips_instance(nics))
                       for vm, nics in vms_and_nics]
        return [dict(vm_name=vm.resource_name, ips=[self._get_ip_dict(ip)
                                                    for ip in ips]) for vm, ips in vms_and_ips if len(ips) > 0]

    def _get_dependencies(self, dep_tree, resource_type):
        matches = [value for value in dep_tree.values() if value['dep'].resource_type == resource_type]
        for child_tree in [value['children'] for value in dep_tree.values()]:
            matches += self._get_dependencies(child_tree, resource_type)
        return matches

    def _build_hierarchy(self, dependencies, tree=None):
        tree = dict(top=True) if tree is None else tree
        for dep in dependencies:
            if dep.resource_name not in tree:
                tree[dep.resource_name] = dict(dep=dep, children=dict())
            if isinstance(dep, self.rm_models.Dependency) and dep.depends_on is not None and len(dep.depends_on) > 0:
                self._build_hierarchy(dep.depends_on, tree[dep.resource_name]['children'])

        if 'top' in tree:
            tree.pop('top', None)
            keys = list(tree.keys())
            for key1 in keys:
                for key2 in keys:
                    if key2 in tree and key1 in tree[key2]['children'] and key1 in tree:
                        tree[key2]['children'][key1] = tree[key1]
                        tree.pop(key1)
        return tree

    def _get_ip_dict(self, ip):
        ip_dict = dict(name=ip.name,
                       id=ip.id,
                       public_ip=ip.ip_address,
                       public_ip_allocation_method=str(ip.public_ip_allocation_method)
                       )
        if ip.dns_settings:
            ip_dict['dns_settings'] = {
                'domain_name_label': ip.dns_settings.domain_name_label,
                'fqdn': ip.dns_settings.fqdn
            }
        return ip_dict

    def _nic_to_public_ips_instance(self, nics):
        return [self.network_client.public_ip_addresses.get(public_ip_id.split('/')[4], public_ip_id.split('/')[-1])
                for nic_obj in (self.network_client.network_interfaces.get(self.resource_group_name,
                                                                           nic['dep'].resource_name) for nic in nics)
                for public_ip_id in [ip_conf_instance.public_ip_address.id
                                     for ip_conf_instance in nic_obj.ip_configurations
                                     if ip_conf_instance.public_ip_address]]


def main():
    AzureRMDeploymentManager()


if __name__ == '__main__':
    main()
