# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: vmware
    plugin_type: inventory
    short_description: VMware inventory source
    description:
        - Get inventory hosts from VMware environment.
        - Uses any file which ends with vmware.yml or vmware.yaml as a YAML configuration file.
    extends_documentation_fragment:
      - constructed
      - inventory_cache
    options:
        hostname:
            description: Name of vCenter or ESXi server
            env:
              - name: VMWARE_SERVER
        username:
            description: Name of vSphere admin user
            env:
              - name: VMWARE_USERNAME
        password:
            description: Password of vSphere admin user
            env:
              - name: VMWARE_PASSWORD
        port:
            description: Port number used to connect to vCenter or ESXi Server
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
            - Requires 'vSphere Automation SDK' and 'vCloud Suite SDK' libraries to be installed on the given controller machine.
            - Please refer following URLs for installation steps
            - 'https://code.vmware.com/web/sdk/65/vsphere-automation-python'
            - 'https://code.vmware.com/web/sdk/60/vcloudsuite-python'
            default: False
            type: boolean
'''

EXAMPLES = '''
simple_config_file:

    plugin: vmware
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True

'''

import ssl
import atexit

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

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'vmware'

    def _set_params(self):
        """
        Function to set credentials
        """
        self.hostname = self._options.get('hostname')
        self.username = self._options.get('username')
        self.password = self._options.get('password')
        self.port = self._options.get('port') or 443
        self.with_tags = self._options.get('with_tags', False)

        self.validate_certs = self._options.get('validate_certs')

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

    def login_vapi(self):
        """
        Function to login to vCenter API using REST call
        Returns: connection object

        """
        session = requests.Session()
        session.verify = self.validate_certs
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

    def login(self):
        """
        Function to login to vCenter or ESXi server
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

    def verify_file(self, path):
        """
        Function to verify plugin configuration file and mark this plugin active
        Args:
            path: Path of configuration YAML file

        Returns: True if everything is correct, else False

        """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('vmware.yaml', 'vmware.yml')):
                valid = True
        if not HAS_REQUESTS or not HAS_PYVMOMI:
            valid = False
        return valid

    def parse(self, inventory, loader, path, cache=False):
        """
        parses the inventory file
        """

        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        self._set_params()
        self.content = self.login()
        self.rest_content = self.login_vapi()

        self._populate_from_source()

    def _populate_from_source(self):
        """
        Function to populate inventory data from direct source

        """
        cacheable_results = {}
        hostvars = {}
        objects = self.get_managed_objects_properties(vim_type=vim.VirtualMachine, properties=['name'])

        tag_svc = Tag(self.rest_content)
        tag_association = TagAssociation(self.rest_content)

        tags_info = dict()
        tags = tag_svc.list()
        for tag in tags:
            tag_obj = tag_svc.get(tag)
            tags_info[tag_obj.id] = tag_obj.name
            if tag_obj.name not in cacheable_results:
                cacheable_results[tag_obj.name] = {'hosts': []}
                self.inventory.add_group(tag_obj.name)

        for temp_vm_object in objects:
            for temp_vm_object_property in temp_vm_object.propSet:
                # VMware does not provide a way to uniquely identify VM by its name
                # i.e. there can be two virtual machines with same name
                # Appending "_" and VMware UUID to make it unique
                current_host = temp_vm_object_property.val + "_" + temp_vm_object.obj.config.uuid

                if current_host not in hostvars:
                    hostvars[current_host] = {}
                    self.inventory.add_host(current_host)

                    # Only gather facts related to tag if vCloud and vSphere is installed.
                    if HAS_VCLOUD and HAS_VSPHERE:
                        # Add virtual machine to appropriate tag group
                        vm_mo_id = temp_vm_object.obj._GetMoId()
                        vm_dynamic_id = DynamicID(type='VirtualMachine', id=vm_mo_id)
                        attached_tags = tag_association.list_attached_tags(vm_dynamic_id)

                        for tag_id in attached_tags:
                            self.inventory.add_child(tags_info[tag_id], current_host)
                            cacheable_results[tags_info[tag_id]]['hosts'].append(current_host)

                    # Based on power state of virtual machine
                    vm_power = temp_vm_object.obj.summary.runtime.powerState
                    if vm_power not in cacheable_results:
                        cacheable_results[vm_power] = []
                        self.inventory.add_group(vm_power)
                    cacheable_results[vm_power].append(current_host)
                    self.inventory.add_child(vm_power, current_host)
        return cacheable_results

    def get_managed_objects_properties(self, vim_type, properties=None):
        """
        Function to look up a Managed Object Reference in vCenter / ESXi Environment
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
