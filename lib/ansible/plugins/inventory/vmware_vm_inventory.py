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
        validate_certs:
            description:
            - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
            default: True
            type: boolean
        with_tags:
            description:
            - Include tags and associated virtual machines.
            - Requires 'vSphere Automation SDK' library to be installed on the given controller machine.
            - Please refer following URLs for installation steps
            - 'https://code.vmware.com/web/sdk/65/vsphere-automation-python'
            default: False
            type: boolean
        properties:
            description:
            - Specify the list of VMware schema properties associated with the VM.
            - These properties will be populated in hostvars of the given VM.
            - Each value in the list specifies the path to a specific property in VM object.
            type: list
            default: [ 'name', 'config.cpuHotAddEnabled', 'config.cpuHotRemoveEnabled',
                       'config.instanceUuid', 'config.hardware.numCPU', 'config.template',
                       'config.name', 'guest.hostName', 'guest.ipAddress',
                       'guest.guestId', 'guest.guestState', 'runtime.maxMemoryUsage',
                       'runtime.powerState', 'customValue'
                       ]
            version_added: "2.9"
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

# Gather minimum set of properties for VMware guest
    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: False
    properties:
    - 'name'
    - 'guest.ipAddress'

# Gather full set of properties for VMware guests
    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$
    with_tags: False
    properties:
    - 'name'
    - 'customValue'
    - 'capability.secureBootSupported'
    - 'capability.nestedHVSupported'
    - 'config.annotation'
    - 'config.alternateGuestName'
    - 'config.bootOptions.bootDelay'
    - 'config.bootOptions.bootRetryDelay'
    - 'config.bootOptions.bootRetryEnabled'
    - 'config.bootOptions.enterBIOSSetup'
    - 'config.bootOptions.efiSecureBootEnabled'
    - 'config.bootOptions.networkBootProtocol'
    - 'config.cpuAllocation.limit'
    - 'config.cpuAllocation.reservation'
    - 'config.cpuAllocation.shares.level'
    - 'config.cpuAllocation.shares.shares'
    - 'config.cpuFeatureMask.eax'
    - 'config.cpuFeatureMask.ebx'
    - 'config.cpuFeatureMask.ecx'
    - 'config.cpuFeatureMask.edx'
    - 'config.cpuFeatureMask.level'
    - 'config.cpuFeatureMask.vendor'
    - 'config.cpuHotAddEnabled'
    - 'config.cpuHotRemoveEnabled'
    - 'config.instanceUuid'
    - 'config.firmware'
    - 'config.guestAutoLockEnabled'
    - 'config.hardware.memoryMB'
    - 'config.hardware.numCoresPerSocket'
    - 'config.hardware.numCPU'
    - 'config.hardware.virtualICH7MPresent'
    - 'config.hardware.virtualSMCPresent'
    - 'config.hotPlugMemoryIncrementSize'
    - 'config.hotPlugMemoryLimit'
    - 'config.memoryAllocation.limit'
    - 'config.memoryAllocation.reservation'
    - 'config.memoryAllocation.shares.level'
    - 'config.memoryAllocation.shares.shares'
    - 'config.memoryHotAddEnabled'
    - 'config.memoryReservationLockedToMax'
    - 'config.nestedHVEnabled'
    - 'config.scheduledHardwareUpgradeInfo.scheduledHardwareUpgradeStatus'
    - 'config.scheduledHardwareUpgradeInfo.upgradePolicy'
    - 'config.scheduledHardwareUpgradeInfo.versionKey'
    - 'config.template'
    - 'config.name'
    - 'guest.hostName'
    - 'guest.ipAddress'
    - 'config.tools.afterPowerOn'
    - 'config.tools.afterResume'
    - 'config.tools.beforeGuestReboot'
    - 'config.tools.beforeGuestShutdown'
    - 'config.tools.beforeGuestStandby'
    - 'config.tools.pendingCustomization'
    - 'config.tools.syncTimeWithHost'
    - 'config.tools.toolsUpgradePolicy'
    - 'config.tools.toolsVersion'
    - 'config.version'
    - 'guest.guestFamily'
    - 'guest.guestFullName'
    - 'guest.guestId'
    - 'guest.guestKernelCrashed'
    - 'guest.guestOperationsReady'
    - 'guest.guestState'
    - 'guest.interactiveGuestOperationsReady'
    - 'guest.toolsInstallType'
    - 'guest.toolsRunningStatus'
    - 'guest.toolsUpdateStatus'
    - 'guest.toolsVersion'
    - 'guest.toolsVersionStatus2'
    - 'guestHeartbeatStatus'
    - 'runtime.bootTime'
    - 'runtime.cleanPowerOff'
    - 'runtime.connectionState'
    - 'runtime.consolidationNeeded'
    - 'runtime.cryptoState'
    - 'runtime.dasVmProtection.dasProtected'
    - 'runtime.faultToleranceState'
    - 'runtime.maxCpuUsage'
    - 'runtime.maxMemoryUsage'
    - 'runtime.onlineStandby'
    - 'runtime.paused'
    - 'runtime.powerState'
    - 'runtime.snapshotInBackground'
    - 'runtime.suspendInterval'
    - 'runtime.suspendTime'
    - 'runtime.toolsInstallerMounted'
    - 'runtime.vFlashCacheAllocation'
    - 'summary.config.numEthernetCards'
    - 'summary.config.numVirtualDisks'
    - 'summary.config.tpmPresent'
    - 'summary.storage.committed'
    - 'summary.storage.uncommitted'
    - 'summary.storage.unshared'
    - 'summary.overallStatus'
'''

import ssl
import atexit
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
    from com.vmware.vapi.std_client import DynamicID
    from vmware.vapi.vsphere.client import create_vsphere_client
    HAS_VSPHERE = True
except ImportError:
    HAS_VSPHERE = False


from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable

# Overwrite _ALWAYS_SAFE to only include letters and number
# so that everything is correctly quoted
try:
    # python3
    import urllib.parse
    urllib.parse._ALWAYS_SAFE = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                          b'abcdefghijklmnopqrstuvwxyz'
                                          b'0123456789')
    urllib.parse._ALWAYS_SAFE_BYTES = bytes(urllib.parse._ALWAYS_SAFE)
except ImportError:
    # python2
    import urllib
    from past.builtins import xrange
    urllib.always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                          'abcdefghijklmnopqrstuvwxyz'
                          '0123456789')
    urllib._safe_map = {}
    for i, c in zip(xrange(256), str(bytearray(xrange(256)))):
        urllib._safe_map[c] = c if (i < 128 and c in urllib.always_safe) else '%{0:02x}'.format(i)
    urllib.parse = urllib  # fake pyton3 structure, so that python3 syntax can be used afterwards


class BaseVMwareInventory:
    def __init__(self, hostname, username, password, port, validate_certs, with_tags):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.with_tags = with_tags
        self.validate_certs = validate_certs
        self.content = None
        self.rest_content = None

    def do_login(self):
        """
        Check requirements and do login
        """
        self.check_requirements()
        self.content = self._login()
        if self.with_tags:
            self.rest_content = self._login_vapi()

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

        client = create_vsphere_client(server=self.hostname,
                                       username=self.username,
                                       password=self.password,
                                       session=session)
        if client is None:
            raise AnsibleError("Failed to login to %s using %s" % (self.hostname, self.username))
        return client

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

        if not all([self.hostname, self.username, self.password]):
            raise AnsibleError("Missing one of the following : hostname, username, password. Please read "
                               "the documentation for more information.")

    def _get_managed_objects_properties(self, vim_type, properties=None):
        """
        Look up a Managed Object Reference in vCenter / ESXi Environment
        :param vim_type: Type of vim object e.g, for datacenter - vim.Datacenter
        :param properties: List of properties related to vim object e.g. Name
        :return: local content object
        """
        # Get Root Folder
        root_folder = self.content.rootFolder

        if properties is None:
            properties = ['name']

        # Create Container View with default root folder
        mor = self.content.viewManager.CreateContainerView(root_folder, [vim_type], True)

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
            hostname=self.get_option('hostname'),
            username=self.get_option('username'),
            password=self.get_option('password'),
            port=self.get_option('port'),
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
                source_data = self._cache[cache_key]
            except KeyError:
                update_cache = True

        using_current_cache = cache and not update_cache
        cacheable_results = self._populate_from_source(source_data, using_current_cache)

        if update_cache:
            self._cache[cache_key] = cacheable_results

    def _get_fullName(self, vm_obj_obj):
        """
          This is based on the url schema VMware uses within the PowerCLI api
          but the PowerCLI url has collisions, as it uses slashes as folder name
          deliminator, but slashes can also occur within folder names themselves
          in the original these slashes are not escaped and the resulting path
          is inaccessible or even worse it overlays another path and the action
          could be performed on the vms within the wrong folder.
          To prevent this issue, every foldername within the folderpath gets
          urlencode before constructing
          There is also an instanceUUID, but that is never shown to the user, so users
          are not able to recognize the correct vm that way.
          Not to be confuse with the uuid which is the UUID of the SMBios, it is not
          guaranteed to be unique, as it does not necessarily change if a vm is imported
          or copied.
          VM names and folders are not restricted to specific characters either,
          so foldernames need to be encoded first and transformed into a pseudo path.
        """
        if(vm_obj_obj.parent):
            return self._get_fullName(vm_obj_obj.parent) + '/' + urllib.parse.quote_plus(vm_obj_obj.name, safe='')
        else:
            # For some reason the api returns 'Datencenter' (not Datacenter) as the
            # root item, but VMware has also not included it within there path schema,
            # instead they have added the hostname and the port of the instance.
            # So why not mirror that as well?
            # That way we can differentiate vms between multiple isolated vmware instances.
            return 'vis:/' + self.pyv.hostname + '@' + str(self.pyv.port)

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

        vm_properties = set(self.get_option('properties')) or set()

        cacheable_results = {'_meta': {'hostvars': {}}}
        hostvars = {}

        # It's way faster to fetch all wanted properties right now.
        # Otherwise they are fetched when we try to access them for the first time
        # and as we're looping over the list the properties would be fetched at a one by one basis
        # resulting in linear instead of konstant execution time.
        query_properties = [x for x in vm_properties if x != "customValue"] or ["name"]
        objects = self.pyv._get_managed_objects_properties(vim_type=vim.VirtualMachine,
                                                           properties=query_properties)

        if self.pyv.with_tags:
            tag_svc = self.pyv.rest_content.tagging.Tag
            tag_association = self.pyv.rest_content.tagging.TagAssociation

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
                if not vm_obj.obj.config:
                    # Sometime orphaned VMs return no configurations
                    continue
                # VMware does not provide a way to uniquely identify a VM by its name
                # i.e. there can be two virtual machines with same name
                # The full name instead is unique and recognizable to users.
                current_host = self._get_fullName(vm_obj.obj)

                if current_host not in hostvars:
                    hostvars[current_host] = {}
                    self.inventory.add_host(current_host)

                    self._populate_host_properties(vm_obj, current_host, vm_properties)

                    # Only gather facts related to tag if vCloud and vSphere is installed.
                    if HAS_VSPHERE and self.pyv.with_tags:
                        self.inventory.set_variable(current_host, 'vmware.with_tags', True)
                        vm_mo_id = vm_obj.obj._GetMoId()
                        vm_dynamic_id = DynamicID(type='VirtualMachine', id=vm_mo_id)
                        attached_tags = tag_association.list_attached_tags(vm_dynamic_id)

                        for tag_id in attached_tags:
                            # TODO: Test and set value to false if tag is not attached
                            self.inventory.set_variable(current_host, 'vmware.tags.' + tags_info[tag_id], True)
                            self.inventory.add_child(tags_info[tag_id], current_host)
                            cacheable_results[tags_info[tag_id]]['hosts'].append(current_host)

                    # Based on power state of virtual machine
                    if "runtime.powerState" in vm_properties:
                        vm_power = str(self.pyv._get_object_prop(vm_obj.obj, ["runtime", "powerState"]))
                        if vm_power not in cacheable_results:
                            cacheable_results[vm_power] = {'hosts': []}
                            self.inventory.add_group(vm_power)
                        cacheable_results[vm_power]['hosts'].append(current_host)
                        self.inventory.add_child(vm_power, current_host)

                    # Based on guest id
                    if "guest.guestId" in vm_properties:
                        vm_guest_id = str(self.pyv._get_object_prop(vm_obj.obj, ["guest", "guestId"]))
                        if vm_guest_id and vm_guest_id not in cacheable_results:
                            cacheable_results[vm_guest_id] = {'hosts': []}
                            self.inventory.add_group(vm_guest_id)
                        cacheable_results[vm_guest_id]['hosts'].append(current_host)
                        self.inventory.add_child(vm_guest_id, current_host)

                    # Based on folder of virtual machine
                    folders = current_host.split('/')
                    if folders[-2] not in cacheable_results:
                        parent_folders = []
                        self.inventory.add_group(folders[0])
                        cacheable_results[folders[0]] = {'hosts': [], 'children': []}
                        while len(folders) > 1:
                            parent_folders.append(folders.pop(0))
                            parent_folder_path = '/'.join(parent_folders)

                            if len(folders) > 1:
                                current_folder = folders[0]
                                current_folder_path = parent_folder_path + '/' + current_folder
                                if current_folder_path not in cacheable_results:
                                    self.inventory.add_group(current_folder_path)
                                    self.inventory.add_child(parent_folder_path, current_folder_path)
                                    cacheable_results[parent_folder_path]['children'].append(current_folder_path)
                                    cacheable_results[current_folder_path] = {'hosts': [], 'children': []}
                            else:
                                cacheable_results[parent_folder_path]['hosts'].append(current_host)
                                self.inventory.add_child(parent_folder_path, current_host)

        for host in hostvars:
            h = self.inventory.get_host(host)
            cacheable_results['_meta']['hostvars'][h.name] = h.vars

        return cacheable_results

    def _populate_host_properties(self, vm_obj, current_host, vm_properties):
        if "customValue" in vm_properties:
            field_mgr = []
            if self.pyv.content.customFieldsManager:
                field_mgr = self.pyv.content.customFieldsManager.field
            for cust_value in vm_obj.obj.customValue:
                self.inventory.set_variable(
                    current_host,
                    [y.name for y in field_mgr if y.key == cust_value.key][0],
                    cust_value.value
                )
            vm_properties.remove("customValue")

        for vm_prop in vm_properties:
            vm_value = self.pyv._get_object_prop(vm_obj.obj, vm_prop.split("."))
            if type(vm_value) not in [int, str]:
                # Some values are enums with a custom vmware specific type
                # for simplicity just convert every returned type we don't
                # expect to a string.
                if vm_value is None:
                    continue
                else:
                    vm_value = str(vm_value)
            self.inventory.set_variable(current_host, vm_prop, vm_value)

        # ansible_host
        if "guest.ipAddress" in vm_properties:
            primary_host_ip = vm_obj.obj.guest.ipAddress
            if primary_host_ip:
                self.inventory.set_variable(current_host, 'ansible_host', primary_host_ip)

        # guest.hostDomainName
        if "guest.hostName" in vm_properties:
            host_FQDN = str(vm_obj.obj.guest.hostName)
            host_domain_name = '.'.join(host_FQDN.split(".")[1:])
            self.inventory.set_variable(current_host, 'guest.hostDomainName', host_domain_name)

        # Add the full path of the vm to the variables
        self.inventory.set_variable(current_host, 'path', current_host)

        # Set inventory variables, so that if multiple inventories are used one can differentiate
        # to which host/vcenter the vm belongs to (e.g. production or staging)
        self.inventory.set_variable(current_host, 'vmware.hostname', self.pyv.hostname)
        self.inventory.set_variable(current_host, 'vmware.port', self.pyv.port)
        self.inventory.set_variable(current_host, 'vmware.validate_certs', self.pyv.validate_certs)
        self.inventory.set_variable(current_host, 'vmware.with_tags', False)
