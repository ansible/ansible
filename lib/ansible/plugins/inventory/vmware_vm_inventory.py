#
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: vmware_vm_inventory
    plugin_type: inventory
    short_description: VMware Guest inventory source
    version_added: "2.7"
    author:
      - Abhijeet Kasurde (@Akasurde)
    description:
        - Get virtual machines as inventory hosts from VMware environment.
        - Uses any file which ends with vmware.yml or vmware.yaml as a YAML configuration file.
        - The inventory_hostname is always the 'Name' and UUID of the virtual machine. UUID is added as VMware allows virtual machines with the same name.
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
              - Datacenter name. 
              - Required if C(search_folder) or C(with_folders) are set, otherwise ignored.
            version_added: "2.8"
            required: False
        hostname:
            description: Name of vCenter or ESXi server.
            required: True
            env:
              - name: VMWARE_SERVER
        username:
            description: Name of vSphere admin user.
            required: True
            env:
              - name: VMWARE_USERNAME
        password:
            description: Password of vSphere admin user.
            required: True
            env:
              - name: VMWARE_PASSWORD
        port:
            description: Port number used to connect to vCenter or ESXi Server.
            default: 443
            env:
              - name: VMWARE_PORT
        search_folder:
            description: Inventory path for the root folder of the VM search. Requires `datacenter` to be set.
            required: False
            type: str
            version_added: "2.8"
        validate_certs:
            description:
            - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
            default: True
            type: boolean
        with_folders:
            description: Create groups based on the folder hierarchy of the VCenter Inventory. Requires  `datacenter` to be set.
            default: False
            type: boolean
            version_added: "2.8"
        with_tags:
            description:
            - Include tags and associated virtual machines.
            - Requires 'vSphere Automation SDK' and 'vCloud Suite SDK' libraries to be installed on the given controller machine.
            - Please refer following URLs for installation steps
            - 'https://code.vmware.com/web/sdk/65/vsphere-automation-python'
            - 'https://code.vmware.com/web/sdk/60/vcloudsuite-python'
            default: False
            type: boolean
'''

EXAMPLES = '''
# Sample configuration file for VMware Guest dynamic inventory
    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True

# Example limiting the inventory to a subfolder, and creating groups based on folders
    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True
    datacenter: MyDC
    with_folders: True
    search_folder: Folder1/SubFolderA
'''

import ssl
import atexit
from collections import namedtuple
from ansible.errors import AnsibleError, AnsibleParserError

try:
    # requests is required for exception handling of the ConnectionError
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

try:
    from vmware.vapi.lib.connect import get_requests_connector
    from vmware.vapi.security.session import create_session_security_context
    from vmware.vapi.security.user_password import create_user_password_security_context
    from com.vmware.cis_client import Session
    from com.vmware.vapi.std_client import DynamicID
    from com.vmware.cis.tagging_client import Tag, TagAssociation
    HAS_VCLOUD = True
except ImportError:
    HAS_VCLOUD = False

try:
    from vmware.vapi.stdlib.client.factories import StubConfigurationFactory
    HAS_VSPHERE = True
except ImportError:
    HAS_VSPHERE = False

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class BaseVMwareInventory:
    def __init__(self, datacenter, hostname, username, password, port, search_folder, validate_certs, with_folders, with_tags):
        self.datacenter = datacenter
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.search_folder = search_folder
        self.with_folders = with_folders
        self.with_tags = with_tags
        self.validate_certs = validate_certs
        self.content = None
        self.rest_content = None

        # Slashes are significant to our folder logic, so let's make sure we sanitize the input
        if self.search_folder:
            self.search_folder = self.search_folder.strip('/')
        if self.datacenter:
            self.datacenter = self.datacenter.strip('/')

    def do_login(self):
        """
        Check requirements and do login
        """
        self.check_requirements()
        self.content = self._login()
        if self.with_tags:
            self.rest_content = self._login_vapi()

        # Get the folder object that will serve as our inventory root folder
        if self.search_folder:
            self.root_folder = self.content.searchIndex.FindByInventoryPath('%s/vm/%s' % (self.datacenter, self.search_folder))
            if not self.root_folder:
                raise AnsibleError("Specified datacenter + search_folder '%s/vm/%s' were not found on Inventory." %
                                   (self.datacenter, self.search_folder))
        elif self.with_folders:
            self.root_folder = self.content.searchIndex.FindByInventoryPath('%s/vm' % self.datacenter)
            if not self.root_folder:
                raise AnsibleError("Specified datacenter '%s' was not found on Inventory." % self.datacenter)
        else:
            self.root_folder = self.content.rootFolder

    def _login_vapi(self):
        """
        Login to vCenter API using REST call
        Returns: connection object

        """
        session = requests.Session()
        session.verify = self.validate_certs
        if not self.validate_certs:
            # Disable warning shown at stdout
            requests.packages.urllib3.disable_warnings()

        vcenter_url = "https://%s/api" % self.hostname

        # Get request connector
        connector = get_requests_connector(session=session, url=vcenter_url)
        # Create standard Configuration
        stub_config = StubConfigurationFactory.new_std_configuration(connector)
        # Use username and password in the security context to authenticate
        security_context = create_user_password_security_context(self.username, self.password)
        # Login
        stub_config.connector.set_security_context(security_context)
        # Create the stub for the session service and login by creating a session.
        session_svc = Session(stub_config)
        session_id = session_svc.create()

        # After successful authentication, store the session identifier in the security
        # context of the stub and use that for all subsequent remote requests
        session_security_context = create_session_security_context(session_id)
        stub_config.connector.set_security_context(session_security_context)

        if stub_config is None:
            raise AnsibleError("Failed to login to %s using %s" % (self.hostname, self.username))
        return stub_config

    def _login(self):
        """
        Login to vCenter or ESXi server
        Returns: connection object

        """
        if self.validate_certs and not hasattr(ssl, 'SSLContext'):
            raise AnsibleError('pyVim does not support changing verification mode with python < 2.7.9. Either update '
                               'python or set validate_certs to false in configuration YAML file.')

        ssl_context = None
        if not self.validate_certs and hasattr(ssl, 'SSLContext'):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            ssl_context.verify_mode = ssl.CERT_NONE

        service_instance = None
        try:
            service_instance = connect.SmartConnect(host=self.hostname, user=self.username,
                                                    pwd=self.password, sslContext=ssl_context,
                                                    port=self.port)
        except vim.fault.InvalidLogin as e:
            raise AnsibleParserError("Unable to log on to vCenter or ESXi API at %s:%s as %s: %s" % (self.hostname, self.port, self.username, e.msg))
        except vim.fault.NoPermission as e:
            raise AnsibleParserError("User %s does not have required permission"
                                     " to log on to vCenter or ESXi API at %s:%s : %s" % (self.username, self.hostname, self.port, e.msg))
        except (requests.ConnectionError, ssl.SSLError) as e:
            raise AnsibleParserError("Unable to connect to vCenter or ESXi API at %s on TCP/%s: %s" % (self.hostname, self.port, e))
        except vmodl.fault.InvalidRequest as e:
            # Request is malformed
            raise AnsibleParserError("Failed to get a response from server %s:%s as "
                                     "request is malformed: %s" % (self.hostname, self.port, e.msg))
        except Exception as e:
            raise AnsibleParserError("Unknown error while connecting to vCenter or ESXi API at %s:%s : %s" % (self.hostname, self.port, e))

        if service_instance is None:
            raise AnsibleParserError("Unknown error while connecting to vCenter or ESXi API at %s:%s" % (self.hostname, self.port))

        atexit.register(connect.Disconnect, service_instance)
        return service_instance.RetrieveContent()

    def check_requirements(self):
        """ Check all requirements for this inventory are satisified"""
        if not HAS_REQUESTS:
            raise AnsibleParserError('Please install "requests" Python module as this is required'
                                     ' for VMware Guest dynamic inventory plugin.')
        elif not HAS_PYVMOMI:
            raise AnsibleParserError('Please install "PyVmomi" Python module as this is required'
                                     ' for VMware Guest dynamic inventory plugin.')
        if HAS_REQUESTS:
            # Pyvmomi 5.5 and onwards requires requests 2.3
            # https://github.com/vmware/pyvmomi/blob/master/requirements.txt
            required_version = (2, 3)
            requests_version = requests.__version__.split(".")[:2]
            try:
                requests_major_minor = tuple(map(int, requests_version))
            except ValueError:
                raise AnsibleParserError("Failed to parse 'requests' library version.")

            if requests_major_minor < required_version:
                raise AnsibleParserError("'requests' library version should"
                                         " be >= %s, found: %s." % (".".join([str(w) for w in required_version]),
                                                                    requests.__version__))

        if not HAS_VSPHERE and self.with_tags:
            raise AnsibleError("Unable to find 'vSphere Automation SDK' Python library which is required."
                               " Please refer this URL for installation steps"
                               " - https://code.vmware.com/web/sdk/65/vsphere-automation-python")

        if not HAS_VCLOUD and self.with_tags:
            raise AnsibleError("Unable to find 'vCloud Suite SDK' Python library which is required."
                               " Please refer this URL for installation steps"
                               " - https://code.vmware.com/web/sdk/60/vcloudsuite-python")

        if not all([self.hostname, self.username, self.password]):
            raise AnsibleError("Missing one of the following : hostname, username, password. Please read "
                               "the documentation for more information.")

        if (self.with_folders or self.search_folder) and not self.datacenter:
            raise AnsibleError("You must set the 'datacenter' param when setting either 'search_folder' "
                               "or 'with_folders'.")

    def _get_managed_objects_properties(self, vim_type, properties=None):
        """
        Look up a Managed Object Reference in vCenter / ESXi Environment
        :param vim_type: Type of vim object e.g, for datacenter - vim.Datacenter
        :param properties: List of properties related to vim object e.g. Name
        :return: local content object
        """
        if properties is None:
            properties = ['name']

        # Create Container View on root folder
        mor = self.content.viewManager.CreateContainerView(self.root_folder, [vim_type], True)

        # Create Traversal spec
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
            name="traversal_spec",
            path='view',
            skip=False,
            type=vim.view.ContainerView
        )

        # Create Property Spec
        property_spec = vmodl.query.PropertyCollector.PropertySpec(
            type=vim_type,  # Type of object to retrieved
            all=False,
            pathSet=properties
        )

        # Create Object Spec
        object_spec = vmodl.query.PropertyCollector.ObjectSpec(
            obj=mor,
            skip=True,
            selectSet=[traversal_spec]
        )

        # Create Filter Spec
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=[object_spec],
            propSet=[property_spec],
            reportMissingObjectsInResults=False
        )

        return self.content.propertyCollector.RetrieveContents([filter_spec])

    @staticmethod
    def _get_object_prop(vm, attributes):
        """Safely get a property or return None"""
        result = vm
        for attribute in attributes:
            try:
                result = getattr(result, attribute)
            except (AttributeError, IndexError):
                return None
        return result


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'vmware_vm_inventory'

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
            datacenter=self.get_option('datacenter'),
            hostname=self.get_option('hostname'),
            username=self.get_option('username'),
            password=self.get_option('password'),
            port=self.get_option('port'),
            search_folder=self.get_option('search_folder'),
            with_folders=self.get_option('with_folders'),
            with_tags=self.get_option('with_tags'),
            validate_certs=self.get_option('validate_certs')
        )

        self.pyv.do_login()

        self.pyv.check_requirements()

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

    def _create_folder_groups(self, folder_objects, cacheable_results):
        """
        Creates groups matching the folder hierarchy in vCenter

        folder_objects is the result of a _get_managed_objects_properties call with vim_type set to vim.Folder.
        This only create the groups in the inventory, it does not associate any VMs to them.
        """
        # This function walks through the provided folder_objects, and builds
        # an auxiliary dict self.vcenter_folders. That dict will hold a map
        # from vmware's folder object ID to a namedtuple that holds:
        # - The folder actual name
        # - The folder *path* (relative to the root datacenter_folder/vm/)
        # - The ansible group name, derived from the path
        # - The folder children, which exists only so we can build the path
        #
        # This vcenter_folder exists mainly because I didn't figure it out a
        # property of the vim.VirtualMachine object that already holds the
        # path. If that exists, please tell me and we can replace this.
        #
        # We will use that map later to add each discovered hosts to the right
        # ansible group.

        def path2group_name(path):
            'A quick function to create an ansible group name derived from a vCenter folder path'
            return path.strip('/').replace('/', '_').lower()

        VcenterFolder = namedtuple('VcenterFolder', ['name', 'path', 'children', 'ansible_group_name'])

        # The map starts with self.root_folder. If a search_folder was
        # specified, we will create it as a parent group (that it would be
        # the same as the all group in practice). We do this because we want
        # that running the inventory limited to a search_folder or not should
        # yield the same groups and group names for the VMs inside the search
        # folder.
        #
        # The slashes (/) are significant for the group names, so we take caution
        # of handling then consistently.
        if self.pyv.search_folder:
            root_folder_path = '/%s/' % self.pyv.search_folder
        else:
            root_folder_path = '/'
        self.vcenter_folders = {self.pyv.root_folder: VcenterFolder(
            name=self.pyv.root_folder.name,
            path=root_folder_path,
            children=[],
            ansible_group_name=path2group_name(root_folder_path),
        )}

        for temp_folder_object in folder_objects:
            folder_obj = temp_folder_object.obj
            path = '%s%s/' % (self.vcenter_folders[folder_obj.parent].path, folder_obj.name)
            self.vcenter_folders[folder_obj] = VcenterFolder(
                name=folder_obj.name,
                path=path,
                children=[],
                ansible_group_name=path2group_name(path),
            )
            self.vcenter_folders[folder_obj.parent].children.append(self.vcenter_folders[folder_obj])

        for folder in self.vcenter_folders.values():
            if folder.ansible_group_name != '':
                self.inventory.add_group(folder.ansible_group_name)
                cacheable_results[folder.ansible_group_name] = {'hosts': [], 'groups': []}

        for folder in self.vcenter_folders.values():
            if folder.ansible_group_name != '':
                for child in folder.children:
                    self.inventory.add_child(folder.ansible_group_name, child.ansible_group_name)
                    cacheable_results[folder.ansible_group_name]['groups'].append(child.ansible_group_name)

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
        # add child subgroups to groups
        # this cannot be done in the loop above because both groups must have been created already
        for group in source_data:
            if group == 'all':
                continue
            else:
                sub_groups = source_data[group].get('groups', [])
                for sub_group in sub_groups:
                    self.inventory.add_child(group, sub_group)
        if not source_data:
            for host in hostvars:
                self.inventory.add_host(host)
                self._populate_host_vars([host], hostvars.get(host, {}))

    def _populate_from_source(self, source_data, using_current_cache):
        """
        Populate inventory data from direct source

        """
        if using_current_cache:
            self._populate_from_cache(source_data)
            return source_data

        cacheable_results = {'_meta': {'hostvars': {}}}
        hostvars = {}

        if self.pyv.with_folders:
            self._create_folder_groups(self.pyv._get_managed_objects_properties(vim_type=vim.Folder, properties=['name']), cacheable_results)

        objects = self.pyv._get_managed_objects_properties(vim_type=vim.VirtualMachine,
                                                           properties=['name'])

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

        for vm_obj in objects:
            for vm_obj_property in vm_obj.propSet:
                # VMware does not provide a way to uniquely identify VM by its name
                # i.e. there can be two virtual machines with same name
                # Appending "_" and VMware UUID to make it unique
                current_host = vm_obj_property.val + "_" + vm_obj.obj.config.uuid

                if current_host not in hostvars:
                    hostvars[current_host] = {}
                    self.inventory.add_host(current_host)

                    host_ip = vm_obj.obj.guest.ipAddress
                    if host_ip:
                        self.inventory.set_variable(current_host, 'ansible_host', host_ip)

                    self._populate_host_properties(vm_obj, current_host)

                    # Only gather facts related to tag if vCloud and vSphere is installed.
                    if HAS_VCLOUD and HAS_VSPHERE and self.pyv.with_tags:
                        # Add virtual machine to appropriate tag group
                        vm_mo_id = vm_obj.obj._GetMoId()
                        vm_dynamic_id = DynamicID(type='VirtualMachine', id=vm_mo_id)
                        attached_tags = tag_association.list_attached_tags(vm_dynamic_id)

                        for tag_id in attached_tags:
                            self.inventory.add_child(tags_info[tag_id], current_host)
                            cacheable_results[tags_info[tag_id]]['hosts'].append(current_host)

                    # Based on power state of virtual machine
                    vm_power = str(vm_obj.obj.summary.runtime.powerState)
                    if vm_power not in cacheable_results:
                        cacheable_results[vm_power] = {'hosts': []}
                        self.inventory.add_group(vm_power)
                    cacheable_results[vm_power]['hosts'].append(current_host)
                    self.inventory.add_child(vm_power, current_host)

                    # Based on guest id
                    vm_guest_id = vm_obj.obj.config.guestId
                    if vm_guest_id and vm_guest_id not in cacheable_results:
                        cacheable_results[vm_guest_id] = {'hosts': []}
                        self.inventory.add_group(vm_guest_id)
                    cacheable_results[vm_guest_id]['hosts'].append(current_host)
                    self.inventory.add_child(vm_guest_id, current_host)

                    # Based on folder
                    if self.pyv.with_folders:
                        folder_group_name = self.vcenter_folders[vm_obj.obj.parent].ansible_group_name
                        if folder_group_name != '':
                            cacheable_results[folder_group_name]['hosts'].append(current_host)
                            self.inventory.add_child(folder_group_name, current_host)

        for host in hostvars:
            h = self.inventory.get_host(host)
            cacheable_results['_meta']['hostvars'][h.name] = h.vars

        return cacheable_results

    def _populate_host_properties(self, vm_obj, current_host):
        # Load VM properties in host_vars
        vm_properties = [
            'name',
            'config.cpuHotAddEnabled',
            'config.cpuHotRemoveEnabled',
            'config.instanceUuid',
            'config.hardware.numCPU',
            'config.template',
            'config.name',
            'guest.hostName',
            'guest.ipAddress',
            'guest.guestId',
            'guest.guestState',
            'runtime.maxMemoryUsage',
            'customValue',
        ]
        field_mgr = self.pyv.content.customFieldsManager.field

        for vm_prop in vm_properties:
            if vm_prop == 'customValue':
                for cust_value in vm_obj.obj.customValue:
                    self.inventory.set_variable(current_host,
                                                [y.name for y in field_mgr if y.key == cust_value.key][0],
                                                cust_value.value)
            else:
                vm_value = self.pyv._get_object_prop(vm_obj.obj, vm_prop.split("."))
                self.inventory.set_variable(current_host, vm_prop, vm_value)
