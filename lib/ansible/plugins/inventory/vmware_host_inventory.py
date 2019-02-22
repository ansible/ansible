#
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: vmware_host_inventory
    plugin_type: inventory
    short_description: VMware Host inventory source
    version_added: "2.8"
    authors:
        - Abhijeet Kasurde (@Akasurde)
    description:
        - Get ESXi host system as inventory hosts from VMware environment.
        - Uses any file which ends with vmware.yml or vmware.yaml as a YAML configuration file.
        - The inventory_hostname is always the 'Name' and UUID of the host systems.
        - UUID is added as VMware allows ESXi host system with the same name.
    extends_documentation_fragment:
      - inventory_cache
    requirements:
      - "Python >= 2.7"
      - "PyVmomi"
      - "requests >= 2.3"
      - "vSphere Automation SDK - For tag feature"
      - "vCloud Suite SDK - For tag feature"
    options:
      datacenter:
        description:
        - The name of datacenter to be used to gather inventory.
        type: str
      hostname:
        description: Name of vCenter server.
        required: True
        type: str
        env:
        - name: VMWARE_SERVER
      username:
        description: Name of vSphere admin user.
        required: True
        type: str
        env:
        - name: VMWARE_USERNAME
      password:
        description: Password of vSphere admin user.
        required: True
        type: str
        env:
        - name: VMWARE_PASSWORD
      port:
        description: Port number used to connect to vCenter server.
        default: 443
        type: str
        env:
        - name: VMWARE_PORT
      validate_certs:
        description:
        - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
        default: True
        type: boolean
      with_tags:
        description:
        - Include tags and associated host systems.
        - Requires 'vSphere Automation SDK' and 'vCloud Suite SDK' libraries to be installed on the given controller machine.
        - Please refer following URLs for installation steps
        - 'https://code.vmware.com/web/sdk/65/vsphere-automation-python'
        - 'https://code.vmware.com/web/sdk/60/vcloudsuite-python'
        default: False
        type: boolean
      properties:
        description:
        - Specify the list of Property associated with host system.
        - These properties will be populated in hostvars of the given host system.
        - Each value in list specifies the path to a specific property in host system object.
        type: list
        default: [ name, summary.hardware.model, summary.hardware.vendor, summary.hardware.uuid, summary.hardware.memorySize,
                   summary.hardware.cpuModel, summary.hardware.cpuMhz, summary.hardware.numCpuPkgs, summary.hardware.numCpuCores,
                   summary.hardware.numCpuThreads, summary.hardware.numNics, summary.hardware.numHBAs, config.product.name, config.product.fullName,
                   config.product.vendor, config.product.version, config.product.build, config.product.localeVersion, config.product.localeBuild,
                   config.product.osType, config.product.productLineId, config.product.apiType, config.product.apiVersion, config.product.instanceUuid,
                   config.product.licenseProductName, config.product.licenseProductVersion ]
'''

EXAMPLES = '''
# Sample configuration file for VMware Host System dynamic inventory
    plugin: vmware_host_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True

# Sample configuration file for VMware host system dynamic inventory with specific properties
    plugin: vmware_host_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: False
    properties:
        - name
        - summary.hardware.model
        - summary.hardware.vendor
        - summary.hardware.uuid
        - summary.hardware.memorySize
        - summary.hardware.cpuModel
        - summary.hardware.cpuMhz
        - config.product.version
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

try:
    from com.vmware.vapi.std_client import DynamicID
    from com.vmware.cis.tagging_client import Tag, TagAssociation
    HAS_VCLOUD = True
except ImportError:
    HAS_VCLOUD = False

from ansible.errors import AnsibleError
from ansible.plugins.inventory.vmware_vm_inventory import BaseVMwareInventory
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'vmware_host_inventory'

    def verify_file(self, path):
        """
        Verify plugin configuration file and mark this plugin active
        Args:
            path: Path of configuration YAML file

        Returns: True if everything is correct, else False

        """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('vmware.yaml', 'vmware.yml')):
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=True):
        """
        Parses the inventory file
        """
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        cache_key = self.get_cache_key(path)

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        self.pyv = BaseVMwareInventory(
            hostname=self.get_option('hostname'),
            username=self.get_option('username'),
            password=self.get_option('password'),
            port=self.get_option('port'),
            with_tags=self.get_option('with_tags'),
            validate_certs=self.get_option('validate_certs'),
        )

        self.pyv.do_login()

        self.pyv.datacenter = self.get_option('datacenter')

        source_data = None
        if cache:
            cache = self.get_option('cache')

        update_cache = False
        if cache:
            try:
                source_data = self.cache.get(cache_key)
            except KeyError:
                update_cache = True

        using_current_cache = cache and not update_cache
        cacheable_results = self._populate_from_source(source_data, using_current_cache)

        if update_cache:
            self.cache.set(cache_key, cacheable_results)

    def get_host_ip_address(self, host_obj):
        """
        Get Host System IP Address
        """
        ret = None
        vnic_manager = host_obj.configManager.virtualNicManager
        if not vnic_manager:
            return ret

        # Query all management nics
        query = vnic_manager.QueryNetConfig('management')
        selected_vnics = [vnic for vnic in query.selectedVnic]
        mgmt_vnics = [vnic for vnic in query.candidateVnic if vnic.key in selected_vnics]

        if not mgmt_vnics:
            return ret

        try:
            # We return first found member
            return mgmt_vnics[0].spec.ip.ipAddress
        except (IndexError, AttributeError):
            return ret

    def _populate_from_cache(self, source_data):
        """ Populate cache using source data """
        hostvars = source_data.pop('_meta', {}).get('hostvars', {})
        for group in source_data:
            if group == 'all':
                continue
            else:
                self.inventory.add_group(group)
                hosts = source_data[group].get('hosts', [])
                for host in hosts:
                    self._populate_host_vars([host], hostvars.get(host, {}), group)
                self.inventory.add_child('all', group)

    def _populate_from_source(self, source_data, using_current_cache):
        """
        Populate inventory data from direct source

        """
        if using_current_cache:
            self._populate_from_cache(source_data)
            return source_data

        cacheable_results = {'_meta': {'hostvars': {}}}
        hostvars = {}

        dc_obj = None
        root_folder = None

        if self.pyv.datacenter:
            dc_obj = self.pyv.get_datacenter_obj(self.pyv.datacenter)
            if dc_obj is None:
                raise AnsibleError("Datacenter name %s specified but no such object found" % self.pyv.datacenter)

        if dc_obj:
            root_folder = dc_obj.hostFolder

        objects = self.pyv._get_managed_objects_properties(vim_type=vim.HostSystem, properties=['name'], folder=root_folder)

        if self.pyv.with_tags:
            tag_svc = Tag(self.pyv.rest_content)
            tag_association = TagAssociation(self.pyv.rest_content)

            tags_info = dict()
            tags = tag_svc.list()
            for tag in tags:
                tag_obj = tag_svc.get(tag)
                tags_info[tag_obj.id] = tag_obj.name
                if tag_obj.name not in cacheable_results:
                    cacheable_results[tag_obj.name] = {'hosts': []}
                    self.inventory.add_group(tag_obj.name)

        for host_obj in objects:
            for host_obj_property in host_obj.propSet:
                # VMware does not provide a way to uniquely identify VM by its name
                # i.e. there can be two virtual machines with same name
                # Appending "_" and VMware UUID to make it unique
                current_host = host_obj_property.val + "_" + host_obj.obj.summary.hardware.uuid

                if current_host not in hostvars:
                    hostvars[current_host] = {}
                    self.inventory.add_host(current_host)

                    host_ip = self.get_host_ip_address(host_obj.obj)
                    if host_ip:
                        self.inventory.set_variable(current_host, 'ansible_host', host_ip)

                    # Load Host properties in host_vars
                    host_properties = self.get_option('properties') or []
                    for host_prop in host_properties:
                        host_value = self.pyv._get_object_prop(host_obj.obj, host_prop.split("."))
                        self.inventory.set_variable(current_host, host_prop, host_value)

                    # Only gather facts related to tag if vCloud and vSphere is installed.
                    if HAS_VCLOUD and self.pyv.with_tags:
                        # Add virtual machine to appropriate tag group
                        host_mo_id = host_obj.obj._GetMoId()
                        vm_dynamic_id = DynamicID(type='HostSystem', id=host_mo_id)
                        attached_tags = tag_association.list_attached_tags(vm_dynamic_id)

                        for tag_id in attached_tags:
                            self.inventory.add_child(tags_info[tag_id], current_host)
                            cacheable_results[tags_info[tag_id]]['hosts'].append(current_host)

                    # Based on power state of virtual machine
                    host_power = str(host_obj.obj.summary.runtime.powerState)
                    if host_power not in cacheable_results:
                        cacheable_results[host_power] = {'hosts': []}
                        self.inventory.add_group(host_power)
                    cacheable_results[host_power]['hosts'].append(current_host)
                    self.inventory.add_child(host_power, current_host)

        for host in hostvars:
            h = self.inventory.get_host(host)
            cacheable_results['_meta']['hostvars'][h.name] = h.vars

        return cacheable_results
