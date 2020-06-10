#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_template
short_description: Module to manage virtual machine templates in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage virtual machine templates in oVirt/RHV."
options:
    name:
        description:
            - "Name of the template to manage."
    id:
        description:
            - "ID of the template to be registered."
        version_added: "2.4"
    state:
        description:
            - "Should the template be present/absent/exported/imported/registered.
               When C(state) is I(registered) and the unregistered template's name
               belongs to an already registered in engine template in the same DC
               then we fail to register the unregistered template."
        choices: ['present', 'absent', 'exported', 'imported', 'registered']
        default: present
    vm:
        description:
            - "Name of the VM, which will be used to create template."
    description:
        description:
            - "Description of the template."
    cpu_profile:
        description:
            - "CPU profile to be set to template."
    cluster:
        description:
            - "Name of the cluster, where template should be created/imported."
    allow_partial_import:
        description:
            - "Boolean indication whether to allow partial registration of a template when C(state) is registered."
        type: bool
        version_added: "2.4"
    vnic_profile_mappings:
        description:
            - "Mapper which maps an external virtual NIC profile to one that exists in the engine when C(state) is registered.
               vnic_profile is described by the following dictionary:"
        suboptions:
            source_network_name:
                description:
                    - The network name of the source network.
            source_profile_name:
                description:
                    - The profile name related to the source network.
            target_profile_id:
                description:
                    - The id of the target profile id to be mapped to in the engine.
        version_added: "2.5"
    cluster_mappings:
        description:
            - "Mapper which maps cluster name between Template's OVF and the destination cluster this Template should be registered to,
               relevant when C(state) is registered.
               Cluster mapping is described by the following dictionary:"
        suboptions:
            source_name:
                description:
                    - The name of the source cluster.
            dest_name:
                description:
                    - The name of the destination cluster.
        version_added: "2.5"
    role_mappings:
        description:
            - "Mapper which maps role name between Template's OVF and the destination role this Template should be registered to,
               relevant when C(state) is registered.
               Role mapping is described by the following dictionary:"
        suboptions:
            source_name:
                description:
                    - The name of the source role.
            dest_name:
                description:
                    - The name of the destination role.
        version_added: "2.5"
    domain_mappings:
        description:
            - "Mapper which maps aaa domain name between Template's OVF and the destination aaa domain this Template should be registered to,
               relevant when C(state) is registered.
               The aaa domain mapping is described by the following dictionary:"
        suboptions:
            source_name:
                description:
                    - The name of the source aaa domain.
            dest_name:
                description:
                    - The name of the destination aaa domain.
        version_added: "2.5"
    exclusive:
        description:
            - "When C(state) is I(exported) this parameter indicates if the existing templates with the
               same name should be overwritten."
        type: bool
    export_domain:
        description:
            - "When C(state) is I(exported) or I(imported) this parameter specifies the name of the
               export storage domain."
    image_provider:
        description:
            - "When C(state) is I(imported) this parameter specifies the name of the image provider to be used."
    image_disk:
        description:
            - "When C(state) is I(imported) and C(image_provider) is used this parameter specifies the name of disk
               to be imported as template."
        aliases: ['glance_image_disk_name']
    io_threads:
        description:
            - "Number of IO threads used by virtual machine. I(0) means IO threading disabled."
        version_added: "2.7"
    template_image_disk_name:
        description:
            - "When C(state) is I(imported) and C(image_provider) is used this parameter specifies the new name for imported disk,
               if omitted then I(image_disk) name is used by default.
               This parameter is used only in case of importing disk image from Glance domain."
        version_added: "2.4"
    storage_domain:
        description:
            - "When C(state) is I(imported) this parameter specifies the name of the destination data storage domain.
               When C(state) is I(registered) this parameter specifies the name of the data storage domain of the unregistered template."
    clone_permissions:
        description:
            - "If I(True) then the permissions of the VM (only the direct ones, not the inherited ones)
            will be copied to the created template."
            - "This parameter is used only when C(state) I(present)."
        type: bool
        default: False
    seal:
        description:
            - "'Sealing' is an operation that erases all machine-specific configurations from a filesystem:
               This includes SSH keys, UDEV rules, MAC addresses, system ID, hostname, etc.
               If I(true) subsequent virtual machines made from this template will avoid configuration inheritance."
            - "This parameter is used only when C(state) I(present)."
        default: False
        type: bool
        version_added: "2.5"
    operating_system:
        description:
            - Operating system of the template.
            - Default value is set by oVirt/RHV engine.
            - "Possible values: debian_7, freebsd, freebsdx64, other, other_linux, other_linux_kernel_4,
               other_linux_ppc64, other_linux_s390x, other_ppc64, other_s390x, rhcos_x64, rhel_3,
               rhel_3x64, rhel_4, rhel_4x64, rhel_5, rhel_5x64, rhel_6, rhel_6_9_plus_ppc64,
               rhel_6_ppc64, rhel_6x64, rhel_7_ppc64, rhel_7_s390x, rhel_7x64, rhel_8x64,
               rhel_atomic7x64, sles_11, sles_11_ppc64, sles_12_s390x, ubuntu_12_04, ubuntu_12_10,
               ubuntu_13_04, ubuntu_13_10, ubuntu_14_04, ubuntu_14_04_ppc64, ubuntu_16_04_s390x,
               windows_10, windows_10x64, windows_2003, windows_2003x64, windows_2008,
               windows_2008R2x64, windows_2008x64, windows_2012R2x64, windows_2012x64, windows_2016x64,
               windows_2019x64, windows_7, windows_7x64, windows_8, windows_8x64, windows_xp"
        version_added: "2.6"
    memory:
        description:
            - Amount of memory of the template. Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
        version_added: "2.6"
    memory_guaranteed:
        description:
            - Amount of minimal guaranteed memory of the template.
              Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
            - C(memory_guaranteed) parameter can't be lower than C(memory) parameter.
        version_added: "2.6"
    memory_max:
        description:
            - Upper bound of template memory up to which memory hot-plug can be performed.
              Prefix uses IEC 60027-2 standard (for example 1GiB, 1024MiB).
        version_added: "2.6"
    version:
        description:
            - "C(name) - The name of this version."
            - "C(number) - The index of this version in the versions hierarchy of the template. Used for editing of sub template."
        version_added: "2.8"
    clone_name:
        description:
            - Name for importing Template from storage domain.
            - If not defined, C(name) will be used.
        version_added: "2.8"
    usb_support:
        description:
            - "I(True) enable USB support, I(False) to disable it. By default is chosen by oVirt/RHV engine."
        type: bool
        version_added: "2.9"
    timezone:
        description:
            - Sets time zone offset of the guest hardware clock.
            - For example C(Etc/GMT)
        version_added: "2.9"
    sso:
        description:
            - "I(True) enable Single Sign On by Guest Agent, I(False) to disable it. By default is chosen by oVirt/RHV engine."
        type: bool
        version_added: "2.9"
    soundcard_enabled:
        description:
            - "If I(true), the sound card is added to the virtual machine."
        type: bool
        version_added: "2.9"
    smartcard_enabled:
        description:
            - "If I(true), use smart card authentication."
        type: bool
        version_added: "2.9"
    cloud_init:
        description:
            - Dictionary with values for Unix-like Virtual Machine initialization using cloud init.
        suboptions:
            host_name:
                description:
                    - Hostname to be set to Virtual Machine when deployed.
            timezone:
                description:
                    - Timezone to be set to Virtual Machine when deployed.
            user_name:
                description:
                    - Username to be used to set password to Virtual Machine when deployed.
            root_password:
                description:
                    - Password to be set for user specified by C(user_name) parameter.
            authorized_ssh_keys:
                description:
                    - Use this SSH keys to login to Virtual Machine.
            regenerate_ssh_keys:
                description:
                    - If I(True) SSH keys will be regenerated on Virtual Machine.
                type: bool
            custom_script:
                description:
                    - Cloud-init script which will be executed on Virtual Machine when deployed.
                    - This is appended to the end of the cloud-init script generated by any other options.
            dns_servers:
                description:
                    - DNS servers to be configured on Virtual Machine.
            dns_search:
                description:
                    - DNS search domains to be configured on Virtual Machine.
            nic_boot_protocol:
                description:
                    - Set boot protocol of the network interface of Virtual Machine.
                choices: ['none', 'dhcp', 'static']
            nic_ip_address:
                description:
                    - If boot protocol is static, set this IP address to network interface of Virtual Machine.
            nic_netmask:
                description:
                    - If boot protocol is static, set this netmask to network interface of Virtual Machine.
            nic_gateway:
                description:
                    - If boot protocol is static, set this gateway to network interface of Virtual Machine.
            nic_name:
                description:
                    - Set name to network interface of Virtual Machine.
            nic_on_boot:
                description:
                    - If I(True) network interface will be set to start on boot.
                type: bool
        version_added: "2.9"
    cloud_init_nics:
        description:
            - List of dictionaries representing network interfaces to be setup by cloud init.
            - This option is used, when user needs to setup more network interfaces via cloud init.
            - If one network interface is enough, user should use C(cloud_init) I(nic_*) parameters. C(cloud_init) I(nic_*) parameters
              are merged with C(cloud_init_nics) parameters.
        suboptions:
            nic_boot_protocol:
                description:
                    - Set boot protocol of the network interface of Virtual Machine. Can be one of C(none), C(dhcp) or C(static).
            nic_ip_address:
                description:
                    - If boot protocol is static, set this IP address to network interface of Virtual Machine.
            nic_netmask:
                description:
                    - If boot protocol is static, set this netmask to network interface of Virtual Machine.
            nic_gateway:
                description:
                    - If boot protocol is static, set this gateway to network interface of Virtual Machine.
            nic_name:
                description:
                    - Set name to network interface of Virtual Machine.
            nic_on_boot:
                description:
                    - If I(True) network interface will be set to start on boot.
                type: bool
        version_added: "2.9"
    ballooning_enabled:
        description:
            - "If I(true), use memory ballooning."
            - "Memory balloon is a guest device, which may be used to re-distribute / reclaim the host memory
               based on VM needs in a dynamic way. In this way it's possible to create memory over commitment states."
        type: bool
        version_added: "2.9"
    nics:
        description:
            - List of NICs, which should be attached to Virtual Machine. NIC is described by following dictionary.
        suboptions:
            name:
                description:
                    - Name of the NIC.
            profile_name:
                description:
                    - Profile name where NIC should be attached.
            interface:
                description:
                    - Type of the network interface.
                choices: ['virtio', 'e1000', 'rtl8139']
                default: 'virtio'
            mac_address:
                description:
                    - Custom MAC address of the network interface, by default it's obtained from MAC pool.
        version_added: "2.9"
    sysprep:
        description:
            - Dictionary with values for Windows Virtual Machine initialization using sysprep.
        suboptions:
            host_name:
                description:
                    - Hostname to be set to Virtual Machine when deployed.
            active_directory_ou:
                description:
                    - Active Directory Organizational Unit, to be used for login of user.
            org_name:
                description:
                    - Organization name to be set to Windows Virtual Machine.
            domain:
                description:
                    - Domain to be set to Windows Virtual Machine.
            timezone:
                description:
                    - Timezone to be set to Windows Virtual Machine.
            ui_language:
                description:
                    - UI language of the Windows Virtual Machine.
            system_locale:
                description:
                    - System localization of the Windows Virtual Machine.
            input_locale:
                description:
                    - Input localization of the Windows Virtual Machine.
            windows_license_key:
                description:
                    - License key to be set to Windows Virtual Machine.
            user_name:
                description:
                    - Username to be used for set password to Windows Virtual Machine.
            root_password:
                description:
                    - Password to be set for username to Windows Virtual Machine.
        version_added: "2.9"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create template from vm
- ovirt_template:
    cluster: Default
    name: mytemplate
    vm: rhel7
    cpu_profile: Default
    description: Test

# Import template
- ovirt_template:
  state: imported
  name: mytemplate
  export_domain: myexport
  storage_domain: mystorage
  cluster: mycluster

# Remove template
- ovirt_template:
    state: absent
    name: mytemplate

# Change Template Name
- ovirt_template:
    id: 00000000-0000-0000-0000-000000000000
    name: "new_template_name"

# Register template
- ovirt_template:
  state: registered
  storage_domain: mystorage
  cluster: mycluster
  name: mytemplate

# Register template using id
- ovirt_template:
  state: registered
  storage_domain: mystorage
  cluster: mycluster
  id: 1111-1111-1111-1111

# Register template, allowing partial import
- ovirt_template:
  state: registered
  storage_domain: mystorage
  allow_partial_import: "True"
  cluster: mycluster
  id: 1111-1111-1111-1111

# Register template with vnic profile mappings
- ovirt_template:
    state: registered
    storage_domain: mystorage
    cluster: mycluster
    id: 1111-1111-1111-1111
    vnic_profile_mappings:
      - source_network_name: mynetwork
        source_profile_name: mynetwork
        target_profile_id: 3333-3333-3333-3333
      - source_network_name: mynetwork2
        source_profile_name: mynetwork2
        target_profile_id: 4444-4444-4444-4444

# Register template with mapping
- ovirt_template:
    state: registered
    storage_domain: mystorage
    cluster: mycluster
    id: 1111-1111-1111-1111
    role_mappings:
      - source_name: Role_A
        dest_name: Role_B
    domain_mappings:
      - source_name: Domain_A
        dest_name: Domain_B
    cluster_mappings:
      - source_name: cluster_A
        dest_name: cluster_B

# Import image from Glance s a template
- ovirt_template:
    state: imported
    name: mytemplate
    image_disk: "centos7"
    template_image_disk_name: centos7_from_glance
    image_provider: "glance_domain"
    storage_domain: mystorage
    cluster: mycluster

# Edit template subversion
- ovirt_template:
    cluster: mycluster
    name: mytemplate
    vm: rhel7
    version:
        number: 2
        name: subversion

# Create new template subversion
- ovirt_template:
    cluster: mycluster
    name: mytemplate
    vm: rhel7
    version:
        name: subversion

- name: Template with cloud init
  ovirt_template:
    name: mytemplate
    cluster: Default
    memory: 1GiB
    cloud_init:
      nic_boot_protocol: static
      nic_ip_address: 10.34.60.86
      nic_netmask: 255.255.252.0
      nic_gateway: 10.34.63.254
      nic_name: eth1
      nic_on_boot: true
      host_name: example.com
      custom_script: |
        write_files:
         - content: |
             Hello, world!
           path: /tmp/greeting.txt
           permissions: '0644'
      user_name: root
      root_password: super_password

- name: Template with cloud init, with multiple network interfaces
  ovirt_template:
    name: mytemplate
    cluster: mycluster
    cloud_init_nics:
    - nic_name: eth0
      nic_boot_protocol: dhcp
      nic_on_boot: true
    - nic_name: eth1
      nic_boot_protocol: static
      nic_ip_address: 10.34.60.86
      nic_netmask: 255.255.252.0
      nic_gateway: 10.34.63.254
      nic_on_boot: true

- name: Template with timezone and nic
  ovirt_template:
    cluster: MyCluster
    name: mytemplate
    timezone: America/Godthab
    memory_max: 2Gib
    nics:
      - name: nic1

- name: Template with sysprep
  ovirt_vm:
    name: windows2012R2_AD
    cluster: Default
    memory: 3GiB
    sysprep:
      host_name: windowsad.example.com
      user_name: Administrator
      root_password: SuperPassword123
'''

RETURN = '''
id:
    description: ID of the template which is managed
    returned: On success if template is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
template:
    description: "Dictionary of all the template attributes. Template attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/template."
    returned: On success if template is found.
    type: dict
'''

import time
import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    convert_to_bytes,
    create_connection,
    equal,
    get_dict_of_struct,
    get_link_name,
    get_id_by_name,
    ovirt_full_argument_spec,
    search_by_attributes,
    search_by_name,
)


class TemplatesModule(BaseModule):

    def __init__(self, *args, **kwargs):
        super(TemplatesModule, self).__init__(*args, **kwargs)
        self._initialization = None

    def build_entity(self):
        return otypes.Template(
            id=self._module.params['id'],
            name=self._module.params['name'],
            cluster=otypes.Cluster(
                name=self._module.params['cluster']
            ) if self._module.params['cluster'] else None,
            vm=otypes.Vm(
                name=self._module.params['vm']
            ) if self._module.params['vm'] else None,
            description=self._module.params['description'],
            cpu_profile=otypes.CpuProfile(
                id=search_by_name(
                    self._connection.system_service().cpu_profiles_service(),
                    self._module.params['cpu_profile'],
                ).id
            ) if self._module.params['cpu_profile'] else None,
            display=otypes.Display(
                smartcard_enabled=self.param('smartcard_enabled')
            ) if self.param('smartcard_enabled') is not None else None,
            os=otypes.OperatingSystem(
                type=self.param('operating_system'),
            ) if self.param('operating_system') else None,
            memory=convert_to_bytes(
                self.param('memory')
            ) if self.param('memory') else None,
            soundcard_enabled=self.param('soundcard_enabled'),
            usb=(
                otypes.Usb(enabled=self.param('usb_support'))
            ) if self.param('usb_support') is not None else None,
            sso=(
                otypes.Sso(
                    methods=[otypes.Method(id=otypes.SsoMethod.GUEST_AGENT)] if self.param('sso') else []
                )
            ) if self.param('sso') is not None else None,
            time_zone=otypes.TimeZone(
                name=self.param('timezone'),
            ) if self.param('timezone') else None,
            version=otypes.TemplateVersion(
                base_template=self._get_base_template(),
                version_name=self.param('version').get('name'),
            ) if self.param('version') else None,
            memory_policy=otypes.MemoryPolicy(
                guaranteed=convert_to_bytes(self.param('memory_guaranteed')),
                ballooning=self.param('ballooning_enabled'),
                max=convert_to_bytes(self.param('memory_max')),
            ) if any((
                self.param('memory_guaranteed'),
                self.param('ballooning_enabled'),
                self.param('memory_max')
            )) else None,
            io=otypes.Io(
                threads=self.param('io_threads'),
            ) if self.param('io_threads') is not None else None,
            initialization=self.get_initialization(),
        )

    def _get_base_template(self):
        templates = self._connection.system_service().templates_service().list()
        for template in templates:
            if template.version.version_number == 1 and template.name == self.param('name'):
                return otypes.Template(
                    id=template.id
                )

    def post_update(self, entity):
        self.post_present(entity.id)

    def post_present(self, entity_id):
        # After creation of the VM, attach disks and NICs:
        entity = self._service.service(entity_id).get()
        self.__attach_nics(entity)

    def __get_vnic_profile_id(self, nic):
        """
        Return VNIC profile ID looked up by it's name, because there can be
        more VNIC profiles with same name, other criteria of filter is cluster.
        """
        vnics_service = self._connection.system_service().vnic_profiles_service()
        clusters_service = self._connection.system_service().clusters_service()
        cluster = search_by_name(clusters_service, self.param('cluster'))
        profiles = [
            profile for profile in vnics_service.list()
            if profile.name == nic.get('profile_name')
        ]
        cluster_networks = [
            net.id for net in self._connection.follow_link(cluster.networks)
        ]
        try:
            return next(
                profile.id for profile in profiles
                if profile.network.id in cluster_networks
            )
        except StopIteration:
            raise Exception(
                "Profile '%s' was not found in cluster '%s'" % (
                    nic.get('profile_name'),
                    self.param('cluster')
                )
            )

    def __attach_nics(self, entity):
        # Attach NICs to VM, if specified:
        nics_service = self._service.service(entity.id).nics_service()
        for nic in self.param('nics'):
            if search_by_name(nics_service, nic.get('name')) is None:
                if not self._module.check_mode:
                    nics_service.add(
                        otypes.Nic(
                            name=nic.get('name'),
                            interface=otypes.NicInterface(
                                nic.get('interface', 'virtio')
                            ),
                            vnic_profile=otypes.VnicProfile(
                                id=self.__get_vnic_profile_id(nic),
                            ) if nic.get('profile_name') else None,
                            mac=otypes.Mac(
                                address=nic.get('mac_address')
                            ) if nic.get('mac_address') else None,
                        )
                    )
                self.changed = True

    def get_initialization(self):
        if self._initialization is not None:
            return self._initialization

        sysprep = self.param('sysprep')
        cloud_init = self.param('cloud_init')
        cloud_init_nics = self.param('cloud_init_nics') or []
        if cloud_init is not None:
            cloud_init_nics.append(cloud_init)

        if cloud_init or cloud_init_nics:
            self._initialization = otypes.Initialization(
                nic_configurations=[
                    otypes.NicConfiguration(
                        boot_protocol=otypes.BootProtocol(
                            nic.pop('nic_boot_protocol').lower()
                        ) if nic.get('nic_boot_protocol') else None,
                        name=nic.pop('nic_name', None),
                        on_boot=nic.pop('nic_on_boot', None),
                        ip=otypes.Ip(
                            address=nic.pop('nic_ip_address', None),
                            netmask=nic.pop('nic_netmask', None),
                            gateway=nic.pop('nic_gateway', None),
                        ) if (
                            nic.get('nic_gateway') is not None or
                            nic.get('nic_netmask') is not None or
                            nic.get('nic_ip_address') is not None
                        ) else None,
                    )
                    for nic in cloud_init_nics
                    if (
                        nic.get('nic_gateway') is not None or
                        nic.get('nic_netmask') is not None or
                        nic.get('nic_ip_address') is not None or
                        nic.get('nic_boot_protocol') is not None or
                        nic.get('nic_on_boot') is not None
                    )
                ] if cloud_init_nics else None,
                **cloud_init
            )
        elif sysprep:
            self._initialization = otypes.Initialization(
                **sysprep
            )
        return self._initialization

    def update_check(self, entity):
        template_display = entity.display
        return (
            equal(self._module.params.get('cluster'), get_link_name(self._connection, entity.cluster)) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self.param('operating_system'), str(entity.os.type)) and
            equal(self.param('name'), str(entity.name)) and
            equal(self.param('smartcard_enabled'), getattr(template_display, 'smartcard_enabled', False)) and
            equal(self.param('soundcard_enabled'), entity.soundcard_enabled) and
            equal(self.param('ballooning_enabled'), entity.memory_policy.ballooning) and
            equal(self.param('sso'), True if entity.sso.methods else False) and
            equal(self.param('timezone'), getattr(entity.time_zone, 'name', None)) and
            equal(self.param('usb_support'), entity.usb.enabled) and
            equal(convert_to_bytes(self.param('memory_guaranteed')), entity.memory_policy.guaranteed) and
            equal(convert_to_bytes(self.param('memory_max')), entity.memory_policy.max) and
            equal(convert_to_bytes(self.param('memory')), entity.memory) and
            equal(self._module.params.get('cpu_profile'), get_link_name(self._connection, entity.cpu_profile)) and
            equal(self.param('io_threads'), entity.io.threads)
        )

    def _get_export_domain_service(self):
        provider_name = self._module.params['export_domain'] or self._module.params['image_provider']
        export_sds_service = self._connection.system_service().storage_domains_service()
        export_sd = search_by_name(export_sds_service, provider_name)
        if export_sd is None:
            raise ValueError(
                "Export storage domain/Image Provider '%s' wasn't found." % provider_name
            )

        return export_sds_service.service(export_sd.id)

    def post_export_action(self, entity):
        self._service = self._get_export_domain_service().templates_service()

    def post_import_action(self, entity):
        self._service = self._connection.system_service().templates_service()


def _get_role_mappings(module):
    roleMappings = list()

    for roleMapping in module.params['role_mappings']:
        roleMappings.append(
            otypes.RegistrationRoleMapping(
                from_=otypes.Role(
                    name=roleMapping['source_name'],
                ) if roleMapping['source_name'] else None,
                to=otypes.Role(
                    name=roleMapping['dest_name'],
                ) if roleMapping['dest_name'] else None,
            )
        )
    return roleMappings


def _get_domain_mappings(module):
    domainMappings = list()

    for domainMapping in module.params['domain_mappings']:
        domainMappings.append(
            otypes.RegistrationDomainMapping(
                from_=otypes.Domain(
                    name=domainMapping['source_name'],
                ) if domainMapping['source_name'] else None,
                to=otypes.Domain(
                    name=domainMapping['dest_name'],
                ) if domainMapping['dest_name'] else None,
            )
        )
    return domainMappings


def _get_cluster_mappings(module):
    clusterMappings = list()

    for clusterMapping in module.params['cluster_mappings']:
        clusterMappings.append(
            otypes.RegistrationClusterMapping(
                from_=otypes.Cluster(
                    name=clusterMapping['source_name'],
                ),
                to=otypes.Cluster(
                    name=clusterMapping['dest_name'],
                ),
            )
        )
    return clusterMappings


def _get_vnic_profile_mappings(module):
    vnicProfileMappings = list()

    for vnicProfileMapping in module.params['vnic_profile_mappings']:
        vnicProfileMappings.append(
            otypes.VnicProfileMapping(
                source_network_name=vnicProfileMapping['source_network_name'],
                source_network_profile_name=vnicProfileMapping['source_profile_name'],
                target_vnic_profile=otypes.VnicProfile(
                    id=vnicProfileMapping['target_profile_id'],
                ) if vnicProfileMapping['target_profile_id'] else None,
            )
        )

    return vnicProfileMappings


def find_subversion_template(module, templates_service):
    version = module.params.get('version')
    templates = templates_service.list()
    for template in templates:
        if version.get('number') == template.version.version_number and module.params.get('name') == template.name:
            return template

    # when user puts version number which does not exist
    raise ValueError(
        "Template with name '%s' and version '%s' in cluster '%s' was not found'" % (
            module.params['name'],
            module.params['version']['number'],
            module.params['cluster'],
        )
    )


def searchable_attributes(module):
    """
    Return all searchable template attributes passed to module.
    """
    attributes = {
        'name': module.params.get('name'),
        'cluster': module.params.get('cluster'),
    }
    return dict((k, v) for k, v in attributes.items() if v is not None)


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'exported', 'imported', 'registered'],
            default='present',
        ),
        id=dict(default=None),
        name=dict(default=None),
        vm=dict(default=None),
        timezone=dict(type='str'),
        description=dict(default=None),
        sso=dict(type='bool'),
        ballooning_enabled=dict(type='bool', default=None),
        cluster=dict(default=None),
        usb_support=dict(type='bool'),
        allow_partial_import=dict(default=None, type='bool'),
        cpu_profile=dict(default=None),
        clone_permissions=dict(type='bool'),
        export_domain=dict(default=None),
        storage_domain=dict(default=None),
        exclusive=dict(type='bool'),
        clone_name=dict(default=None),
        image_provider=dict(default=None),
        soundcard_enabled=dict(type='bool', default=None),
        smartcard_enabled=dict(type='bool', default=None),
        image_disk=dict(default=None, aliases=['glance_image_disk_name']),
        io_threads=dict(type='int', default=None),
        template_image_disk_name=dict(default=None),
        version=dict(default=None, type='dict'),
        seal=dict(type='bool'),
        vnic_profile_mappings=dict(default=[], type='list'),
        cluster_mappings=dict(default=[], type='list'),
        role_mappings=dict(default=[], type='list'),
        domain_mappings=dict(default=[], type='list'),
        operating_system=dict(type='str'),
        memory=dict(type='str'),
        memory_guaranteed=dict(type='str'),
        memory_max=dict(type='str'),
        nics=dict(type='list', default=[]),
        cloud_init=dict(type='dict'),
        cloud_init_nics=dict(type='list', default=[]),
        sysprep=dict(type='dict'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['id', 'name']],
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        templates_service = connection.system_service().templates_service()
        templates_module = TemplatesModule(
            connection=connection,
            module=module,
            service=templates_service,
        )

        entity = None
        if module.params['version'] is not None and module.params['version'].get('number') is not None:
            entity = find_subversion_template(module, templates_service)

        state = module.params['state']
        if state == 'present':
            force_create = False
            if entity is None and module.params['version'] is not None:
                force_create = True

            ret = templates_module.create(
                entity=entity,
                # When user want to create new template subversion, we must make sure
                # template is force created as it already exists, but new version should be created.
                force_create=force_create,
                result_state=otypes.TemplateStatus.OK,
                search_params=searchable_attributes(module),
                clone_permissions=module.params['clone_permissions'],
                seal=module.params['seal'],
            )
        elif state == 'absent':
            ret = templates_module.remove(entity=entity)
        elif state == 'exported':
            template = templates_module.search_entity()
            if entity is not None:
                template = entity
            export_service = templates_module._get_export_domain_service()
            export_template = search_by_attributes(export_service.templates_service(), id=template.id)

            ret = templates_module.action(
                entity=template,
                action='export',
                action_condition=lambda t: export_template is None or module.params['exclusive'],
                wait_condition=lambda t: t is not None,
                post_action=templates_module.post_export_action,
                storage_domain=otypes.StorageDomain(id=export_service.get().id),
                exclusive=module.params['exclusive'],
            )
        elif state == 'imported':
            template = templates_module.search_entity()
            if entity is not None:
                template = entity
            if template and module.params['clone_name'] is None:
                ret = templates_module.create(
                    result_state=otypes.TemplateStatus.OK,
                )
            else:
                kwargs = {}
                if module.params['image_provider']:
                    kwargs.update(
                        disk=otypes.Disk(
                            name=module.params['template_image_disk_name'] or module.params['image_disk']
                        ),
                        template=otypes.Template(
                            name=module.params['name'] if module.params['clone_name'] is None else module.params['clone_name'],
                        ),
                        clone=True if module.params['clone_name'] is not None else False,
                        import_as_template=True,
                    )

                if module.params['image_disk']:
                    # We need to refresh storage domain to get list of images:
                    templates_module._get_export_domain_service().images_service().list()

                    glance_service = connection.system_service().openstack_image_providers_service()
                    image_provider = search_by_name(glance_service, module.params['image_provider'])
                    images_service = glance_service.service(image_provider.id).images_service()
                else:
                    images_service = templates_module._get_export_domain_service().templates_service()
                template_name = module.params['image_disk'] or module.params['name']
                entity = search_by_name(images_service, template_name)
                if entity is None:
                    raise Exception("Image/template '%s' was not found." % template_name)

                images_service.service(entity.id).import_(
                    storage_domain=otypes.StorageDomain(
                        name=module.params['storage_domain']
                    ) if module.params['storage_domain'] else None,
                    cluster=otypes.Cluster(
                        name=module.params['cluster']
                    ) if module.params['cluster'] else None,
                    **kwargs
                )
                # Wait for template to appear in system:
                template = templates_module.wait_for_import(
                    condition=lambda t: t.status == otypes.TemplateStatus.OK
                )
                ret = templates_module.create(result_state=otypes.TemplateStatus.OK)
                ret = {
                    'changed': True,
                    'id': template.id,
                    'template': get_dict_of_struct(template),
                }
        elif state == 'registered':
            storage_domains_service = connection.system_service().storage_domains_service()
            # Find the storage domain with unregistered template:
            sd_id = get_id_by_name(storage_domains_service, module.params['storage_domain'])
            storage_domain_service = storage_domains_service.storage_domain_service(sd_id)
            templates_service = storage_domain_service.templates_service()

            # Find the unregistered Template we want to register:
            templates = templates_service.list(unregistered=True)
            template = next(
                (t for t in templates if (t.id == module.params['id'] or t.name == module.params['name'])),
                None
            )
            changed = False
            if template is None:
                template = templates_module.search_entity()
                if template is None:
                    raise ValueError(
                        "Template '%s(%s)' wasn't found." % (module.params['name'], module.params['id'])
                    )
            else:
                # Register the template into the system:
                changed = True
                template_service = templates_service.template_service(template.id)
                template_service.register(
                    allow_partial_import=module.params['allow_partial_import'],
                    cluster=otypes.Cluster(
                        name=module.params['cluster']
                    ) if module.params['cluster'] else None,
                    vnic_profile_mappings=_get_vnic_profile_mappings(module)
                    if module.params['vnic_profile_mappings'] else None,
                    registration_configuration=otypes.RegistrationConfiguration(
                        cluster_mappings=_get_cluster_mappings(module),
                        role_mappings=_get_role_mappings(module),
                        domain_mappings=_get_domain_mappings(module),
                    ) if (module.params['cluster_mappings']
                          or module.params['role_mappings']
                          or module.params['domain_mappings']) else None
                )

                if module.params['wait']:
                    template = templates_module.wait_for_import()
                else:
                    # Fetch template to initialize return.
                    template = template_service.get()
                ret = templates_module.create(result_state=otypes.TemplateStatus.OK)
            ret = {
                'changed': changed,
                'id': template.id,
                'template': get_dict_of_struct(template)
            }
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
