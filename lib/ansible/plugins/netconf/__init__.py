#
# (c) 2017 Red Hat Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import abstractmethod
from functools import wraps

from ansible.errors import AnsibleError
from ansible.plugins import AnsiblePlugin
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import missing_required_lib

try:
    from ncclient.operations import RPCError
    from ncclient.xml_ import to_xml, to_ele, NCElement
    HAS_NCCLIENT = True
    NCCLIENT_IMP_ERR = None
except (ImportError, AttributeError) as err:  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False
    NCCLIENT_IMP_ERR = err

try:
    from lxml.etree import Element, SubElement, tostring, fromstring
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring, fromstring


def ensure_ncclient(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not HAS_NCCLIENT:
            raise AnsibleError("%s: %s" % (missing_required_lib('ncclient'), to_native(NCCLIENT_IMP_ERR)))
        return func(self, *args, **kwargs)
    return wrapped


class NetconfBase(AnsiblePlugin):
    """
    A base class for implementing Netconf connections

    .. note:: Unlike most of Ansible, nearly all strings in
        :class:`TerminalBase` plugins are byte strings.  This is because of
        how close to the underlying platform these plugins operate.  Remember
        to mark literal strings as byte string (``b"string"``) and to use
        :func:`~ansible.module_utils._text.to_bytes` and
        :func:`~ansible.module_utils._text.to_text` to avoid unexpected
        problems.

        List of supported rpc's:
            :get: Retrieves running configuration and device state information
            :get_config: Retrieves the specified configuration from the device
            :edit_config: Loads the specified commands into the remote device
            :commit: Load configuration from candidate to running
            :discard_changes: Discard changes to candidate datastore
            :validate: Validate the contents of the specified configuration.
            :lock: Allows the client to lock the configuration system of a device.
            :unlock: Release a configuration lock, previously obtained with the lock operation.
            :copy_config: create or replace an entire configuration datastore with the contents of another complete
                          configuration datastore.
            :get-schema: Retrieves the required schema from the device
            :get_capabilities: Retrieves device information and supported rpc methods

            For JUNOS:
            :execute_rpc: RPC to be execute on remote device
            :load_configuration: Loads given configuration on device

        Note: rpc support depends on the capabilites of remote device.

        :returns: Returns output received from remote device as byte string
        Note: the 'result' or 'error' from response should to be converted to object
              of ElementTree using 'fromstring' to parse output as xml doc

              'get_capabilities()' returns 'result' as a json string.

            Usage:
            from ansible.module_utils.connection import Connection

            conn = Connection()
            data = conn.execute_rpc(rpc)
            reply = fromstring(reply)

            data = conn.get_capabilities()
            json.loads(data)

            conn.load_configuration(config=[''set system ntp server 1.1.1.1''], action='set', format='text')
    """

    __rpc__ = ['rpc', 'get_config', 'get', 'edit_config', 'validate', 'copy_config', 'dispatch', 'lock', 'unlock',
               'discard_changes', 'commit', 'get_schema', 'delete_config', 'get_device_operations']

    def __init__(self, connection):
        super(NetconfBase, self).__init__()
        self._connection = connection

    @property
    def m(self):
        return self._connection.manager

    def rpc(self, name):
        """
        RPC to be execute on remote device
        :param name: Name of rpc in string format
        :return: Received rpc response from remote host
        """
        try:
            obj = to_ele(name)
            resp = self.m.rpc(obj)
            return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
        except RPCError as exc:
            msg = exc.xml
            raise Exception(to_xml(msg))

    def get_config(self, source=None, filter=None):
        """
        Retrieve all or part of a specified configuration
        (by default entire configuration is retrieved).
        :param source: Name of the configuration datastore being queried, defaults to running datastore
        :param filter: This argument specifies the portion of the configuration data to retrieve
        :return: Returns xml string containing the RPC response received from remote host
        """
        if isinstance(filter, list):
            filter = tuple(filter)

        if not source:
            source = 'running'
        resp = self.m.get_config(source=source, filter=filter)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def get(self, filter=None, with_defaults=None):
        """
        Retrieve device configuration and state information.
        :param filter: This argument specifies the portion of the state data to retrieve
                       (by default entire state data is retrieved)
        :param with_defaults: defines an explicit method of retrieving default values
                              from the configuration
        :return: Returns xml string containing the RPC response received from remote host
        """
        if isinstance(filter, list):
            filter = tuple(filter)
        resp = self.m.get(filter=filter, with_defaults=with_defaults)
        response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
        return response

    def edit_config(self, config=None, format='xml', target='candidate', default_operation=None, test_option=None, error_option=None):
        """
        Loads all or part of the specified *config* to the *target* configuration datastore.
        :param config: Is the configuration, which must be rooted in the `config` element.
                       It can be specified either as a string or an :class:`~xml.etree.ElementTree.Element`.
        :param format: The format of configuration eg. xml, text
        :param target: Is the name of the configuration datastore being edited
        :param default_operation: If specified must be one of { `"merge"`, `"replace"`, or `"none"` }
        :param test_option: If specified must be one of { `"test_then_set"`, `"set"` }
        :param error_option: If specified must be one of { `"stop-on-error"`, `"continue-on-error"`, `"rollback-on-error"` }
                             The `"rollback-on-error"` *error_option* depends on the `:rollback-on-error` capability.
        :return: Returns xml string containing the RPC response received from remote host
        """
        if config is None:
            raise ValueError('config value must be provided')
        resp = self.m.edit_config(config, format=format, target=target, default_operation=default_operation, test_option=test_option,
                                  error_option=error_option)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def validate(self, source='candidate'):
        """
        Validate the contents of the specified configuration.
        :param source: Is the name of the configuration datastore being validated or `config` element
                       containing the configuration subtree to be validated
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.validate(source=source)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def copy_config(self, source, target):
        """
        Create or replace an entire configuration datastore with the contents of another complete configuration datastore.
        :param source: Is the name of the configuration datastore to use as the source of the copy operation or `config`
                       element containing the configuration subtree to copy
        :param target: Is the name of the configuration datastore to use as the destination of the copy operation
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.copy_config(source, target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def dispatch(self, rpc_command=None, source=None, filter=None):
        """
        Execute rpc on the remote device eg. dispatch('clear-arp-table')
        :param rpc_command: specifies rpc command to be dispatched either in plain text or in xml element format (depending on command)
        :param source: name of the configuration datastore being queried
        :param filter: specifies the portion of the configuration to retrieve (by default entire configuration is retrieved)
        :return: Returns xml string containing the RPC response received from remote host
        """
        if rpc_command is None:
            raise ValueError('rpc_command value must be provided')

        resp = self.m.dispatch(fromstring(rpc_command), source=source, filter=filter)

        if isinstance(resp, NCElement):
            # In case xml reply is transformed or namespace is removed in
            # ncclient device specific handler return modified xml response
            result = resp.data_xml
        elif hasattr(resp, 'data_ele') and resp.data_ele:
            # if data node is present in xml response return the xml string
            # with data node as root
            result = resp.data_xml
        else:
            # return raw xml string received from host with rpc-reply as the root node
            result = resp.xml

        return result

    def lock(self, target="candidate"):
        """
        Allows the client to lock the configuration system of a device.
        :param target: is the name of the configuration datastore to lock,
                        defaults to candidate datastore
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.lock(target=target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def unlock(self, target="candidate"):
        """
        Release a configuration lock, previously obtained with the lock operation.
        :param target: is the name of the configuration datastore to unlock,
                       defaults to candidate datastore
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.unlock(target=target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def discard_changes(self):
        """
        Revert the candidate configuration to the currently running configuration.
        Any uncommitted changes are discarded.
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.discard_changes()
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def commit(self, confirmed=False, timeout=None, persist=None):
        """
        Commit the candidate configuration as the device's new current configuration.
        Depends on the `:candidate` capability.
        A confirmed commit (i.e. if *confirmed* is `True`) is reverted if there is no
        followup commit within the *timeout* interval. If no timeout is specified the
        confirm timeout defaults to 600 seconds (10 minutes).
        A confirming commit may have the *confirmed* parameter but this is not required.
        Depends on the `:confirmed-commit` capability.
        :param confirmed: whether this is a confirmed commit
        :param timeout: specifies the confirm timeout in seconds
        :param persist: make the confirmed commit survive a session termination,
                        and set a token on the ongoing confirmed commit
        :return: Returns xml string containing the RPC response received from remote host
        """
        timeout = to_text(timeout, errors='surrogate_or_strict')
        resp = self.m.commit(confirmed=confirmed, timeout=timeout, persist=persist)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def get_schema(self, identifier=None, version=None, format=None):
        """
        Retrieve a named schema, with optional revision and type.
        :param identifier: name of the schema to be retrieved
        :param version: version of schema to get
        :param format: format of the schema to be retrieved, yang is the default
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.get_schema(identifier, version=version, format=format)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def delete_config(self, target):
        """
        delete a configuration datastore
        :param target: specifies the  name or URL of configuration datastore to delete
        :return: Returns xml string containing the RPC response received from remote host
        """
        resp = self.m.delete_config(target)
        return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml

    def locked(self, target):
        return self.m.locked(target)

    @abstractmethod
    def get_capabilities(self):
        """
        Retrieves device information and supported
        rpc methods by device platform and return result
        as a string
        :return: Netconf session capability
        """
        pass

    @staticmethod
    def guess_network_os(obj):
        """
        Identifies the operating system of network device.
        :param obj: ncclient manager connection instance
        :return: The name of network operating system.
        """
        pass

    def get_base_rpc(self):
        """
        Returns list of base rpc method supported by remote device
        :return: List of RPC supported
        """
        return self.__rpc__

    def put_file(self, source, destination):
        """
        Copies file to remote host
        :param source: Source location of file
        :param destination: Destination file path
        :return: Returns xml string containing the RPC response received from remote host
        """
        pass

    def fetch_file(self, source, destination):
        """
        Fetch file from remote host
        :param source: Source location of file
        :param destination: Source location of file
        :return: Returns xml string containing the RPC response received from remote host
        """
        pass

    def get_device_operations(self, server_capabilities):
        """
        Retrieve remote host capability from Netconf server hello message.
        :param server_capabilities: Server capabilities received during Netconf session initialization
        :return: Remote host capabilities in dictionary format
        """
        operations = {}
        capabilities = '\n'.join(server_capabilities)
        operations['supports_commit'] = ':candidate' in capabilities
        operations['supports_defaults'] = ':with-defaults' in capabilities
        operations['supports_confirm_commit'] = ':confirmed-commit' in capabilities
        operations['supports_startup'] = ':startup' in capabilities
        operations['supports_xpath'] = ':xpath' in capabilities
        operations['supports_writable_running'] = ':writable-running' in capabilities
        operations['supports_validate'] = ':validate' in capabilities

        operations['lock_datastore'] = []
        if operations['supports_writable_running']:
            operations['lock_datastore'].append('running')

        if operations['supports_commit']:
            operations['lock_datastore'].append('candidate')

        if operations['supports_startup']:
            operations['lock_datastore'].append('startup')

        operations['supports_lock'] = bool(operations['lock_datastore'])

        return operations

# TODO Restore .xml, when ncclient supports it for all platforms
