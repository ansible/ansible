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
            - "Possible values are: debian_7, freebsd, freebsdx64, other, other_linux,
               other_linux_ppc64, other_ppc64, rhel_3, rhel_4, rhel_4x64, rhel_5, rhel_5x64,
               rhel_6, rhel_6x64, rhel_6_ppc64, rhel_7x64, rhel_7_ppc64, sles_11,
               sles_11_ppc64, ubuntu_12_04, ubuntu_12_10, ubuntu_13_04, ubuntu_13_10,
               ubuntu_14_04, ubuntu_14_04_ppc64, windows_10, windows_10x64, windows_2003,
               windows_2003x64, windows_2008, windows_2008x64, windows_2008r2x64,
               windows_2008R2x64, windows_2012x64, windows_2012R2x64,
               windows_7, windows_7x64, windows_8, windows_8x64, windows_xp"
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

# Edit template subeversion
- ovirt_template:
    cluster: mycluster
    name: mytemplate
    vm: rhel7
    version:
        number: 2
        name: subversion

# Create new template subeversion
- ovirt_template:
    cluster: mycluster
    name: mytemplate
    vm: rhel7
    version:
        name: subversion
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
            os=otypes.OperatingSystem(
                type=self.param('operating_system'),
            ) if self.param('operating_system') else None,
            memory=convert_to_bytes(
                self.param('memory')
            ) if self.param('memory') else None,
            version=otypes.TemplateVersion(
                base_template=self._get_base_template(),
                version_name=self.param('version').get('name'),
            ) if self.param('version') else None,
            memory_policy=otypes.MemoryPolicy(
                guaranteed=convert_to_bytes(self.param('memory_guaranteed')),
                max=convert_to_bytes(self.param('memory_max')),
            ) if any((
                self.param('memory_guaranteed'),
                self.param('memory_max')
            )) else None,
            io=otypes.Io(
                threads=self.param('io_threads'),
            ) if self.param('io_threads') is not None else None,
        )

    def _get_base_template(self):
        templates = self._connection.system_service().templates_service().list()
        for template in templates:
            if template.version.version_number == 1 and template.name == self.param('name'):
                return otypes.Template(
                    id=template.id
                )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('cluster'), get_link_name(self._connection, entity.cluster)) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self.param('operating_system'), str(entity.os.type)) and
            equal(self.param('name'), str(entity.name)) and
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
        description=dict(default=None),
        cluster=dict(default=None),
        allow_partial_import=dict(default=None, type='bool'),
        cpu_profile=dict(default=None),
        clone_permissions=dict(type='bool'),
        export_domain=dict(default=None),
        storage_domain=dict(default=None),
        exclusive=dict(type='bool'),
        clone_name=dict(default=None),
        image_provider=dict(default=None),
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
