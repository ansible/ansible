#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
DOCUMENTATION = '''
---
module: azure_deployment
short_description: Create or destroy Azure Resource Manager template deployments
version_added: "2.0"
description:
     - Create or destroy Azure Resource Manager template deployments via the Azure SDK for Python.
       You can find some quick start templates in GitHub here https://github.com/azure/azure-quickstart-templates.
       If you would like to find out more information about Azure Resource Manager templates, see https://azure.microsoft.com/en-us/documentation/articles/resource-group-template-deploy/.
options:
  subscription_id:
    description:
      - The Azure subscription to deploy the template into.
    required: true
  resource_group_name:
    description:
      - The resource group name to use or create to host the deployed template
    required: true
  state:
    description:
      - If state is "present", template will be created.  If state is "present" and if deployment exists, it will be updated.
        If state is "absent", stack will be removed.
    required: true
  template:
    description:
      - A hash containg the templates inline. This parameter is mutually exclusive with 'template_link'.
        Either one of them is required if "state" parameter is "present".
    required: false
    default: None
  template_link:
    description:
      - Uri of file containing the template body. This parameter is mutually exclusive with 'template'. Either one
        of them is required if "state" parameter is "present".
    required: false
    default: None
  parameters:
    description:
      - A hash of all the required template variables for the deployment template. This parameter is mutually exclusive with 'parameters_link'.
        Either one of them is required if "state" parameter is "present".
    required: false
    default: None
  parameters_link:
    description:
      - Uri of file containing the parameters body. This parameter is mutually exclusive with 'parameters'. Either
        one of them is required if "state" parameter is "present".
    required: false
    default: None
  location:
    description:
      - The geo-locations in which the resource group will be located.
    require: false
    default: West US

author: "David Justice (@devigned) / Laurent Mazuel (@lmazuel) / Andre Price (@obsoleted)"
'''

EXAMPLES = '''
# Destroy a template deployment
- name: Destroy Azure Deploy
  azure_deploy:
    state: absent
    subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    resource_group_name: dev-ops-cle

# Create or update a template deployment based on uris to paramters and a template
- name: Create Azure Deploy
  azure_deploy:
    state: present
    subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    resource_group_name: dev-ops-cle
    parameters_link: 'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-simple-linux-vm/azuredeploy.parameters.json'
    template_link: 'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-simple-linux-vm/azuredeploy.json'

# Create or update a template deployment based on a uri to the template and parameters specified inline.
# This deploys a VM with SSH support for a given public key, then stores the result in 'azure_vms'. The result is then used
# to create a new host group. This host group is then used to wait for each instance to respond to the public IP SSH.
---
- hosts: localhost
  tasks:
    - name: Destroy Azure Deploy
      azure_deployment:
        state: absent
        subscription_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        resource_group_name: dev-ops-cle

    - name: Create Azure Deploy
      azure_deployment:
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
      add_host: hostname={{ item['ips'][0].public_ip }} groupname=azure_vms
      with_items: azure.instances

- hosts: azure_vms
  user: devopscle
  tasks:
    - name: Wait for SSH to come up
      wait_for: port=22 timeout=2000 state=started
    - name: echo the hostname of the vm
      shell: hostname

# Deploy an Azure WebApp running a hello world'ish node app
- name: Create Azure WebApp Deployment at http://devopscleweb.azurewebsites.net/hello.js
  azure_deployment:
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
  azure_deploy:
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
            description: "The Ubuntu version for the VM. This will pick a fully patched image of this given Ubuntu version. Allowed values: 12.04.5-LTS, 14.04.2-LTS, 15.04."
      variables:
        location: "West US"
        imagePublisher: "Canonical"
        imageOffer: "UbuntuServer"
        OSDiskName: "osdiskforlinuxsimple"
        nicName: "myVMNic"
        addressPrefix: "10.0.0.0/16"
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
        -
          type: "Microsoft.Storage/storageAccounts"
          name: "[parameters('newStorageAccountName')]"
          apiVersion: "2015-05-01-preview"
          location: "[variables('location')]"
          properties:
            accountType: "[variables('storageAccountType')]"
        -
          apiVersion: "2015-05-01-preview"
          type: "Microsoft.Network/publicIPAddresses"
          name: "[variables('publicIPAddressName')]"
          location: "[variables('location')]"
          properties:
            publicIPAllocationMethod: "[variables('publicIPAddressType')]"
            dnsSettings:
              domainNameLabel: "[parameters('dnsNameForPublicIP')]"
        -
          type: "Microsoft.Network/virtualNetworks"
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
        -
          type: "Microsoft.Network/networkInterfaces"
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
        -
          type: "Microsoft.Compute/virtualMachines"
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
                  uri: "[concat('http://',parameters('newStorageAccountName'),'.blob.core.windows.net/',variables('vmStorageAccountContainerName'),'/',variables('OSDiskName'),'.vhd')]"
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

try:
    import time
    import yaml
    import requests
    import azure
    from itertools import chain
    from azure.common.credentials import BasicTokenAuthentication
    from azure.common.exceptions import CloudError
    from azure.mgmt.resource.resources.models import (
        DeploymentProperties,
        ParametersLink,
        TemplateLink,
        Deployment,
        ResourceGroup,
        Dependency
    )
    from azure.mgmt.resource.resources import ResourceManagementClient, ResourceManagementClientConfiguration
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

AZURE_URL = "https://management.azure.com"


def get_token(domain_or_tenant, client_id, client_secret):
    """
    Get an Azure Active Directory token for a service principal
    :param domain_or_tenant: The domain or tenant id of your Azure Active Directory instance
    :param client_id: The client id of your application in Azure Active Directory
    :param client_secret: One of the application secrets created in your Azure Active Directory application
    :return: an authenticated bearer token to be used with requests to the API
    """
    #  the client id we can borrow from azure xplat cli
    grant_type = 'client_credentials'
    token_url = 'https://login.microsoftonline.com/{}/oauth2/token'.format(domain_or_tenant)

    payload = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': 'https://management.core.windows.net/'
    }

    res = requests.post(token_url, data=payload)
    return res.json()['access_token'] if res.status_code == 200 else None


def get_azure_connection_info(module):
    azure_url = module.params.get('azure_url')
    tenant_or_domain = module.params.get('tenant_or_domain')
    client_id = module.params.get('client_id')
    client_secret = module.params.get('client_secret')
    security_token = module.params.get('security_token')
    resource_group_name = module.params.get('resource_group_name')
    subscription_id = module.params.get('subscription_id')

    if not azure_url:
        if 'AZURE_URL' in os.environ:
            azure_url = os.environ['AZURE_URL']
        else:
            azure_url = None

    if not subscription_id:
        if 'AZURE_SUBSCRIPTION_ID' in os.environ:
            subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        else:
            subscription_id = None

    if not resource_group_name:
        if 'AZURE_RESOURCE_GROUP_NAME' in os.environ:
            resource_group_name = os.environ['AZURE_RESOURCE_GROUP_NAME']
        else:
            resource_group_name = None

    if not security_token:
        if 'AZURE_SECURITY_TOKEN' in os.environ:
            security_token = os.environ['AZURE_SECURITY_TOKEN']
        else:
            security_token = None

    if not tenant_or_domain:
        if 'AZURE_TENANT_ID' in os.environ:
            tenant_or_domain = os.environ['AZURE_TENANT_ID']
        elif 'AZURE_DOMAIN' in os.environ:
            tenant_or_domain = os.environ['AZURE_DOMAIN']
        else:
            tenant_or_domain = None

    if not client_id:
        if 'AZURE_CLIENT_ID' in os.environ:
            client_id = os.environ['AZURE_CLIENT_ID']
        else:
            client_id = None

    if not client_secret:
        if 'AZURE_CLIENT_SECRET' in os.environ:
            client_secret = os.environ['AZURE_CLIENT_SECRET']
        else:
            client_secret = None

    return dict(azure_url=azure_url,
                tenant_or_domain=tenant_or_domain,
                client_id=client_id,
                client_secret=client_secret,
                security_token=security_token,
                resource_group_name=resource_group_name,
                subscription_id=subscription_id)


def build_deployment_body(module):
    """
    Build the deployment body from the module parameters
    :param module: Ansible module containing the validated configuration for the deployment template
    :return: body as dict
    """
    properties = dict(mode='Incremental')
    properties['templateLink'] = \
        dict(uri=module.params.get('template_link'),
             contentVersion=module.params.get('content_version'))

    properties['parametersLink'] = \
        dict(uri=module.params.get('parameters_link'),
             contentVersion=module.params.get('content_version'))

    return dict(properties=properties)

def get_failed_nested_operations(client, resource_group, current_operations):
    new_operations = []
    for operation in current_operations:
        if operation.properties.provisioning_state == 'Failed':
            new_operations.append(operation)
            if operation.properties.target_resource and 'Microsoft.Resources/deployments' in operation.properties.target_resource.id:
                nested_deployment = operation.properties.target_resource.resource_name
                nested_operations = client.deployment_operations.list(resource_group, nested_deployment)
                new_nested_operations = get_failed_nested_operations(client, resource_group, nested_operations)
                new_operations += new_nested_operations

    return new_operations

def get_failed_deployment_operations(module, client, resource_group, deployment_name):
    operations = client.deployment_operations.list(resource_group, deployment_name)
    return [
        dict(
            id=op.id,
            operation_id=op.operation_id,
            status_code=op.properties.status_code,
            status_message=op.properties.status_message,
            target_resource = dict(
                id=op.properties.target_resource.id,
                resource_name=op.properties.target_resource.resource_name,
                resource_type=op.properties.target_resource.resource_type
            ) if op.properties.target_resource else None,
            provisioning_state=op.properties.provisioning_state,
        )
        for op in get_failed_nested_operations(client, resource_group, operations)
    ]

def deploy_template(module, client, conn_info):
    """
    Deploy the targeted template and parameters
    :param module: Ansible module containing the validated configuration for the deployment template
    :param client: resource management client for azure
    :param conn_info: connection info needed
    :return:
    """

    deployment_name = conn_info["deployment_name"]
    group_name = conn_info["resource_group_name"]

    deploy_parameter = DeploymentProperties()
    deploy_parameter.mode = module.params.get('deployment_mode')

    if module.params.get('parameters_link') is None:
        deploy_parameter.parameters = module.params.get('parameters')
    else:
        parameters_link = ParametersLink(
            uri = module.params.get('parameters_link')
        )
        deploy_parameter.parameters_link = parameters_link

    if module.params.get('template_link') is None:
        deploy_parameter.template = module.params.get('template')
    else:
        template_link = TemplateLink(
            uri = module.params.get('template_link')
        )
        deploy_parameter.template_link = template_link

    params = ResourceGroup(location=module.params.get('location'), tags=module.params.get('tags'))
    try:
        client.resource_groups.create_or_update(group_name, params)
        result = client.deployments.create_or_update(group_name, deployment_name, deploy_parameter)
        deployment_result = result.result() # Blocking wait, return the Deployment object
        if module.params.get('wait_for_deployment_completion'):
            while not deployment_result.properties.provisioning_state in {'Canceled', 'Failed', 'Deleted', 'Succeeded'}:
                deployment_result = client.deployments.get(group_name, deployment_name)
                time.sleep(module.params.get('wait_for_deployment_polling_period'))

        if deployment_result.properties.provisioning_state == 'Succeeded':
            return deployment_result

        failed_deployment_operations = get_failed_deployment_operations(module, client, group_name, deployment_name)
        module.fail_json(msg='Deployment failed. Deployment id: %s' % (deployment_result.id), failed_deployment_operations=failed_deployment_operations)
    except CloudError as e:
        module.fail_json(msg='Deploy create failed with status code: %s and message: "%s"' % (e.status_code, e.message))

def destroy_resource_group(module, client, conn_info):
    """
    Destroy the targeted resource group
    :param module: ansible module
    :param client: resource management client for azure
    :param conn_info: connection info needed
    :return: if the result caused a change in the deployment
    """

    try:
        result = client.resource_groups.delete(conn_info['resource_group_name'])
        result.wait() # Blocking wait till the delete is finished
    except CloudError as e:
        if e.status_code == 404 or e.status_code == 204:
            return True
        else:
            module.fail_json(
                msg='Delete resource group and deploy failed with status code: %s and message: %s' % (e.status_code, e.message))


def get_dependencies(dep_tree, resource_type):
    matches = [value for value in dep_tree.values() if value['dep'].resource_type == resource_type]
    for child_tree in [value['children'] for value in dep_tree.values()]:
        matches += get_dependencies(child_tree, resource_type)
    return matches


def build_hierarchy(dependencies, tree=None):
    tree = dict(top=True) if tree is None else tree
    for dep in dependencies:
        if dep.resource_name not in tree:
            tree[dep.resource_name] = dict(dep=dep, children=dict())
        if isinstance(dep, Dependency) and dep.depends_on is not None and len(dep.depends_on) > 0:
            build_hierarchy(dep.depends_on, tree[dep.resource_name]['children'])

    if 'top' in tree:
        tree.pop('top', None)
        keys = list(tree.keys())
        for key1 in keys:
            for key2 in keys:
                if key2 in tree and key1 in tree[key2]['children'] and key1 in tree:
                    tree[key2]['children'][key1] = tree[key1]
                    tree.pop(key1)
    return tree


def get_ip_dict(ip):
    ip_dict = dict(name=ip.name,
                id=ip.id,
                public_ip=ip.ip_address,
                public_ip_allocation_method=str(ip.public_ip_allocation_method))

    if ip.dns_settings:
        ip_dict['dns_settings'] = {
                    'domain_name_label':ip.dns_settings.domain_name_label,
                    'fqdn':ip.dns_settings.fqdn
        }

    return ip_dict


def nic_to_public_ips_instance(client, group, nics):
    return [client.public_ip_addresses.get(group, public_ip_id.split('/')[-1])
              for nic_obj in [client.network_interfaces.get(group, nic['dep'].resource_name) for nic in nics]
              for public_ip_id in [ip_conf_instance.public_ip_address.id for ip_conf_instance in nic_obj.ip_configurations if ip_conf_instance.public_ip_address]]


def get_instances(client, group, deployment):
    dep_tree = build_hierarchy(deployment.properties.dependencies)
    vms = get_dependencies(dep_tree, resource_type="Microsoft.Compute/virtualMachines")

    vms_and_nics = [(vm, get_dependencies(vm['children'], "Microsoft.Network/networkInterfaces")) for vm in vms]
    vms_and_ips = [(vm['dep'], nic_to_public_ips_instance(client, group, nics)) for vm, nics in vms_and_nics]

    return [dict(vm_name=vm.resource_name, ips=[get_ip_dict(ip) for ip in ips]) for vm, ips in vms_and_ips if len(ips) > 0]


def main():
    # import module snippets
    from ansible.module_utils.basic import AnsibleModule
    argument_spec = dict(
        azure_url=dict(default=AZURE_URL),
        subscription_id=dict(),
        client_secret=dict(no_log=True),
        client_id=dict(),
        tenant_or_domain=dict(),
        security_token=dict(aliases=['access_token'], no_log=True),
        resource_group_name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        template=dict(default=None, type='dict'),
        parameters=dict(default=None, type='dict'),
        template_link=dict(default=None),
        parameters_link=dict(default=None),
        location=dict(default="West US"),
        deployment_mode=dict(default='Complete', choices=['Complete', 'Incremental']),
        deployment_name=dict(default="ansible-arm"),
        wait_for_deployment_completion=dict(default=True),
        wait_for_deployment_polling_period=dict(default=30)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['template_link', 'template'], ['parameters_link', 'parameters']],
    )

    if not HAS_DEPS:
        module.fail_json(msg='requests and azure are required for this module')

    conn_info = get_azure_connection_info(module)

    if conn_info['security_token'] is None and \
            (conn_info['client_id'] is None or conn_info['client_secret'] is None or conn_info[
                'tenant_or_domain'] is None):
        module.fail_json(msg='security token or client_id, client_secret and tenant_or_domain is required')

    if conn_info['security_token'] is None:
        conn_info['security_token'] = get_token(conn_info['tenant_or_domain'],
                                                conn_info['client_id'],
                                                conn_info['client_secret'])

    if conn_info['security_token'] is None:
        module.fail_json(msg='failed to retrieve a security token from Azure Active Directory')

    credentials = BasicTokenAuthentication(
        token = {
            'access_token':conn_info['security_token']
        }
    )
    subscription_id = conn_info['subscription_id']
    resource_client = ResourceManagementClient(ResourceManagementClientConfiguration(credentials, subscription_id))
    network_client = NetworkManagementClient(NetworkManagementClientConfiguration(credentials, subscription_id))
    conn_info['deployment_name'] = module.params.get('deployment_name')

    if module.params.get('state') == 'present':
        deployment = deploy_template(module, resource_client, conn_info)
        data = dict(name=deployment.name,
                    group_name=conn_info['resource_group_name'],
                    id=deployment.id,
                    outputs=deployment.properties.outputs,
                    instances=get_instances(network_client, conn_info['resource_group_name'], deployment),
                    changed=True,
                    msg='deployment created')
        module.exit_json(**data)
    else:
        destroy_resource_group(module, resource_client, conn_info)
        module.exit_json(changed=True, msg='deployment deleted')

if __name__ == '__main__':
    main()

