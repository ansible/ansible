#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
#
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_cloud
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of Cloud Avi RESTful Object
description:
    - This module is used to configure Cloud object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    apic_configuration:
        description:
            - Apicconfiguration settings for cloud.
    apic_mode:
        description:
            - Boolean flag to set apic_mode.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    aws_configuration:
        description:
            - Awsconfiguration settings for cloud.
    cloudstack_configuration:
        description:
            - Cloudstackconfiguration settings for cloud.
    dhcp_enabled:
        description:
            - Select the ip address management scheme.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    dns_provider_ref:
        description:
            - Dns profile for the cloud.
            - It is a reference to an object of type ipamdnsproviderprofile.
    docker_configuration:
        description:
            - Dockerconfiguration settings for cloud.
    east_west_dns_provider_ref:
        description:
            - Dns profile for east-west services.
            - It is a reference to an object of type ipamdnsproviderprofile.
    east_west_ipam_provider_ref:
        description:
            - Ipam profile for east-west services.
            - Warning - please use virtual subnets in this ipam profile that do not conflict with the underlay networks or any overlay networks in the cluster.
            - For example in aws and gcp, 169.254.0.0/16 is used for storing instance metadata.
            - Hence, it should not be used in this profile.
            - It is a reference to an object of type ipamdnsproviderprofile.
    enable_vip_static_routes:
        description:
            - Use static routes for vip side network resolution during virtualservice placement.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    ipam_provider_ref:
        description:
            - Ipam profile for the cloud.
            - It is a reference to an object of type ipamdnsproviderprofile.
    license_type:
        description:
            - If no license type is specified then default license enforcement for the cloud type is chosen.
            - The default mappings are container cloud is max ses, openstack and vmware is cores and linux it is sockets.
            - Enum options - LIC_BACKEND_SERVERS, LIC_SOCKETS, LIC_CORES, LIC_HOSTS.
    linuxserver_configuration:
        description:
            - Linuxserverconfiguration settings for cloud.
    mesos_configuration:
        description:
            - Mesosconfiguration settings for cloud.
    mtu:
        description:
            - Mtu setting for the cloud.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1500.
    name:
        description:
            - Name of the object.
        required: true
    nsx_configuration:
        description:
            - Configuration parameters for nsx manager.
            - Field introduced in 17.1.1.
    obj_name_prefix:
        description:
            - Default prefix for all automatically created objects in this cloud.
            - This prefix can be overridden by the se-group template.
    openstack_configuration:
        description:
            - Openstackconfiguration settings for cloud.
    oshiftk8s_configuration:
        description:
            - Oshiftk8sconfiguration settings for cloud.
    prefer_static_routes:
        description:
            - Prefer static routes over interface routes during virtualservice placement.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    proxy_configuration:
        description:
            - Proxyconfiguration settings for cloud.
    rancher_configuration:
        description:
            - Rancherconfiguration settings for cloud.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
    vca_configuration:
        description:
            - Vcloudairconfiguration settings for cloud.
    vcenter_configuration:
        description:
            - Vcenterconfiguration settings for cloud.
    vtype:
        description:
            - Cloud type.
            - Enum options - CLOUD_NONE, CLOUD_VCENTER, CLOUD_OPENSTACK, CLOUD_AWS, CLOUD_VCA, CLOUD_APIC, CLOUD_MESOS, CLOUD_LINUXSERVER, CLOUD_DOCKER_UCP,
            - CLOUD_RANCHER, CLOUD_OSHIFT_K8S.
            - Default value when not specified in API or module is interpreted by Avi Controller as CLOUD_NONE.
        required: true
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create a VMware cloud with write access mode
    avi_cloud:
      username: ''
      controller: ''
      password: ''
      apic_mode: false
      dhcp_enabled: true
      enable_vip_static_routes: false
      license_type: LIC_CORES
      mtu: 1500
      name: VCenter Cloud
      prefer_static_routes: false
      tenant_ref: admin
      vcenter_configuration:
        datacenter_ref: /api/vimgrdcruntime/datacenter-2-10.10.20.100
        management_network: /api/vimgrnwruntime/dvportgroup-103-10.10.20.100
        password: password
        privilege: WRITE_ACCESS
        username: user
        vcenter_url: 10.10.20.100
      vtype: CLOUD_VCENTER
'''
RETURN = '''
obj:
    description: Cloud (api/cloud) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        apic_configuration=dict(type='dict',),
        apic_mode=dict(type='bool',),
        aws_configuration=dict(type='dict',),
        cloudstack_configuration=dict(type='dict',),
        dhcp_enabled=dict(type='bool',),
        dns_provider_ref=dict(type='str',),
        docker_configuration=dict(type='dict',),
        east_west_dns_provider_ref=dict(type='str',),
        east_west_ipam_provider_ref=dict(type='str',),
        enable_vip_static_routes=dict(type='bool',),
        ipam_provider_ref=dict(type='str',),
        license_type=dict(type='str',),
        linuxserver_configuration=dict(type='dict',),
        mesos_configuration=dict(type='dict',),
        mtu=dict(type='int',),
        name=dict(type='str', required=True),
        nsx_configuration=dict(type='dict',),
        obj_name_prefix=dict(type='str',),
        openstack_configuration=dict(type='dict',),
        oshiftk8s_configuration=dict(type='dict',),
        prefer_static_routes=dict(type='bool',),
        proxy_configuration=dict(type='dict',),
        rancher_configuration=dict(type='dict',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        vca_configuration=dict(type='dict',),
        vcenter_configuration=dict(type='dict',),
        vtype=dict(type='str', required=True),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'cloud',
                           set([]))

if __name__ == '__main__':
    main()
